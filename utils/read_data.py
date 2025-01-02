import struct
import numpy as np
import os

###############################################################################
# Basic read_header function
###############################################################################
def read_header(filename):
    """
    Read the Intan File Format header from the given file (RHD or RHS).
    Returns:
    --------
    header : dict
        Dictionary containing read header information.
    """
    fid = open(filename, 'rb')

    header = {}
    filetype = filename[-3:].lower()
    if filetype in ('rhd', 'rhs'):
        header['filetype'] = filetype
    else:
        raise ValueError(f"Unrecognized file extension: {filetype}")

    # Decide if this is .rhd or .rhs
    rhd = (filetype == 'rhd')

    # Check magic number
    magic_number, = struct.unpack('<I', fid.read(4))
    correct_magic_number = int('c6912702', 16) if rhd else int('d69127ac', 16)
    if magic_number != correct_magic_number:
        raise ValueError("Unrecognized file type magic number.")

    header['fid'] = fid
    header['filename'] = filename

    # Read version
    version_major, version_minor = struct.unpack('<hh', fid.read(4))
    header['version'] = {'major': version_major, 'minor': version_minor}

    # Read sample rate
    sample_rate, = struct.unpack('<f', fid.read(4))
    header['sample_rate'] = sample_rate

    # Skip a bunch of fields that are in the original code,
    # but for brevity we'll just seek past them.
    # For .rhs, we know we must skip certain bytes:
    if not rhd:
        # (header['dsp_enabled'], header['actual_dsp_cutoff_frequency'], etc.)
        fid.seek(34, 1)  # skip next 34 bytes

    # Notch filter
    fid.seek(2, 1)  # skip notch filter info

    if not rhd:
        # skip 8 + 4 + 12 more bytes
        fid.seek(8 + 4 + 12, 1)

    # Read the 3 note strings (we won't do anything with them here)
    _ = _read_qstring(fid)  # note1
    _ = _read_qstring(fid)  # note2
    _ = _read_qstring(fid)  # note3

    if rhd:
        # skip potential temperature sensors, board mode, etc.
        fid.seek(4, 1)
        # If version > 1, might have reference channel string:
        if version_major > 1:
            _ = _read_qstring(fid)
    else:
        # skip 4 bytes (dc_amplifier_data_saved, eval_board_mode)
        fid.seek(4, 1)
        # skip reference channel
        _ = _read_qstring(fid)

    # Create dictionary entries
    header['amplifier_channels'] = []
    header['num_amplifier_channels'] = 0

    # The code now reads how many signal groups are present
    number_of_signal_groups, = struct.unpack('<h', fid.read(2))

    for _ in range(number_of_signal_groups):
        signal_group_name = _read_qstring(fid)
        signal_group_prefix = _read_qstring(fid)
        signal_group_enabled, signal_group_num_channels, _ = struct.unpack(
            '<hhh', fid.read(6)
        )

        if (signal_group_num_channels > 0) and (signal_group_enabled > 0):
            for _ in range(signal_group_num_channels):
                native_chan_name = _read_qstring(fid)
                custom_chan_name = _read_qstring(fid)
                # read some channel metadata
                if rhd:
                    unpacked = struct.unpack('<hhhhhh', fid.read(12))
                    signal_type = unpacked[2]
                    channel_enabled = unpacked[3]
                else:
                    unpacked = struct.unpack('<hhhhhhh', fid.read(14))
                    signal_type = unpacked[2]
                    channel_enabled = unpacked[3]

                # skip trigger fields, impedance fields
                fid.seek(8 + 8, 1)

                # We only care about “amplifier” type signals here (signal_type == 0).
                if channel_enabled and (signal_type == 0):
                    header['amplifier_channels'].append({
                        'native_channel_name': native_chan_name,
                        'custom_channel_name': custom_chan_name,
                        'signal_type': signal_type
                    })

    header['num_amplifier_channels'] = len(header['amplifier_channels'])

    # At this point, we've read all the header info we need.
    # Next "header['fid'].tell()" is the place where data blocks begin.
    header['data_start_byte'] = fid.tell()
    header['total_file_size'] = os.path.getsize(filename)

    # For .rhs, each data block has 128 samples
    header['num_samples_per_data_block'] = 128 if not rhd else 60

    # We'll close the file here. When we read data, we can re-open or just do so below.
    fid.close()
    return header


def _read_qstring(fid):
    """Utility to read a Qt style QString. We only do the minimal version of it."""
    length, = struct.unpack('<I', fid.read(4))
    if length == 0xFFFFFFFF:
        return ""
    length = length // 2  # since it's 16-bit Unicode
    data = []
    for _ in range(length):
        c, = struct.unpack('<H', fid.read(2))
        data.append(c)
    return ''.join(chr(c) for c in data)


###############################################################################
# Simplified data-reading function
###############################################################################
def read_intan_rhs_file(file_path):
    """
    Read an Intan .rhs file's header + a single big block of amplifier data.
    Returns:
    --------
    data : dict
        Dictionary with at least 'amplifier_data' as a numpy array,
        shaped as (num_channels, total_samples).
    header : dict
        The header dictionary returned by read_header, plus any expansions.
    """

    # -------------------------------------------------------------------------
    # 1) Read the header
    # -------------------------------------------------------------------------
    header = read_header(file_path)
    num_channels = header['num_amplifier_channels']
    samples_per_block = header['num_samples_per_data_block']

    # Figure out how many data blocks are present. Each block is:
    #   - 4 bytes per sample for the timestamp (128 samples -> 128 * 4 = 512 bytes)
    #   - plus 2 bytes per amplifier channel per sample
    #   - plus other signals we skip, but for .rhs we at least must skip
    #     DC amps, stim, board ADCs, etc.  
    # For simplicity, let's compute total blocks by dividing leftover file size
    # by the known block size. This is a minimal approach (the real code checks more).
    bytes_per_block = _get_bytes_per_data_block(header)
    data_size_bytes = header['total_file_size'] - header['data_start_byte']
    num_data_blocks = data_size_bytes // bytes_per_block

    total_samples = num_data_blocks * samples_per_block

    # -------------------------------------------------------------------------
    # 2) Prepare an array for amplifier data
    # -------------------------------------------------------------------------
    # We'll store raw data (uint16) for each channel x time
    amplifier_data = np.zeros((num_channels, total_samples), dtype=np.uint16)

    # -------------------------------------------------------------------------
    # 3) Read the file again (or re-seek) to parse the amplifier data
    # -------------------------------------------------------------------------
    fid = open(file_path, 'rb')
    fid.seek(header['data_start_byte'], 0)  # move to start of data

    # We skip reading timestamps, stim, etc. and only read amplifier data
    # from each block
    read_offset = 0
    for _ in range(num_data_blocks):
        # Skip timestamp (4 bytes per sample * samples_per_block)
        fid.seek(4 * samples_per_block, 1)

        # Read amplifier data from this block
        # shape is (samples_per_block * num_channels) in 16-bit integers
        block_values = np.fromfile(fid, dtype=np.uint16,
                                   count=samples_per_block * num_channels)
        # Reshape
        block_values = block_values.reshape(num_channels, samples_per_block)
        # Insert into final array
        amplifier_data[:, read_offset:read_offset + samples_per_block] = block_values

        # For .rhs files, there's more data after the amplifier block (DC amplifier, etc.).
        # We have to skip it. We'll do a minimal skip based on the formula:
        skip_this = _rhs_skip_after_amplifier(header)
        fid.seek(skip_this, 1)

        read_offset += samples_per_block

    fid.close()

    # -------------------------------------------------------------------------
    # 4) Bundle data into a dictionary and return
    # -------------------------------------------------------------------------
    data = {
        'amplifier_data': amplifier_data
    }
    return data, header


def _get_bytes_per_data_block(header):
    """
    Minimal version of block size calculation for .rhs (not fully robust, 
    but enough to demonstrate the concept).
    """
    # For RHS:
    #   - 4 bytes * 128 samples for the timestamps
    #   - 2 bytes * (num_amplifier_channels) * 128 for amplifier
    #   - THEN we also have DC amplifier data, stim data, board ADC data, etc.
    # In real code, you'd compute it carefully. Here, we'll do a minimal approach:
    base = 128 * 4  # timestamps
    base += 128 * 2 * header['num_amplifier_channels']  # amplifier
    # Let's guess-skip the rest for demonstration’s sake. The real code is more complex.
    # We'll do a big number to reflect DC amps + stim + ADC + DIG
    # That number is gleaned from the official code or from the Intan docs
    # For demonstration, let's just approximate:
    #   DC amplifier: 128 samples * 2 bytes * numAmplifiers
    #   stim data:    128 samples * 2 bytes * numAmplifiers
    #   plus board ADC, dig in/out, etc. We'll just pretend ~ (some constant times 128).
    # This is just a placeholder for demonstration.
    base += 128 * 2 * header['num_amplifier_channels']  # DC
    base += 128 * 2 * header['num_amplifier_channels']  # stim
    # approximate for board ADC, DAC, dig etc.
    # Let’s do a small constant
    base += 128 * 2 * 2   # pretend 2 board ADC channels
    base += 128 * 2 * 2   # pretend dig in/out lumps
    return base


def _rhs_skip_after_amplifier(header):
    """
    Once we read the amplifier data from each block, we must skip 
    the remainder of that block (DC amplifier, stim, board ADC, dig).
    This function calculates how many bytes to skip. 
    """
    # Since we did a minimal read of only amplifier data, let's skip
    #   DC amps + stim + board ADC + board dig in/out
    # For demonstration, we’ll match what we added in `_get_bytes_per_data_block`
    # after the amplifier data.
    skip_bytes_for_dc = 128 * 2 * header['num_amplifier_channels']
    skip_bytes_for_stim = 128 * 2 * header['num_amplifier_channels']
    skip_bytes_for_adcs = 128 * 2 * 2
    skip_bytes_for_digs = 128 * 2 * 2
    return skip_bytes_for_dc + skip_bytes_for_stim + skip_bytes_for_adcs + skip_bytes_for_digs


###############################################################################
# Example usage
###############################################################################
if __name__ == "__main__":
    file_path = r"C:\Users\eddyt\Documents\Intan recordings\testing\testing2_250102_174724\testing2_250102_174724.rhs"
    data, hdr = read_intan_rhs_file(file_path)

    print("Number of amplifier channels found:", hdr['num_amplifier_channels'])
    print("Amplifier data shape:", data['amplifier_data'].shape)
    print("Sample rate (Hz):", hdr['sample_rate'])

    # Peek at the first 10 samples on the first channel
    first_channel_data = data['amplifier_data'][0, :10]
    print("First 10 samples of channel 0:", first_channel_data)
