import os
import csv
import time
from datetime import datetime
from TCP import RHX_TCPClient

def run_ti_dipole_stimulation(channel_a, channel_b, amplitude_ua1, amplitude_ua2):
    """
    Runs a TI dipole stimulation given two channels and their respective currents.
    
    Parameters
    ----------
    channel_a : str
        The first channel to be stimulated.
    channel_b : str
        The second channel to be stimulated.
    amplitude_ua1 : int
        The stimulation amplitude (in microamps) for channel_a.
    amplitude_ua2 : int
        The stimulation amplitude (in microamps) for channel_b.
    """
    
    # ======================================================================
    # Configuration Parameters
    # ======================================================================
    HOST = "127.0.0.1"
    PORT = 5000

    # Pulse phase duration in microseconds
    PHASE_DURATION_US = 100

    # No interphase delay
    INTERPHASE_DELAY_US = 0

    # Frequencies for the two channels
    FREQ_A = 1200  # Hz
    FREQ_B = 1250  # Hz

    # Convert frequency to pulse train period in microseconds
    # period (µs) = (1/freq) * 1e6
    PERIOD_A_US = int((1.0 / FREQ_A) * 1_000_000)
    PERIOD_B_US = int((1.0 / FREQ_B) * 1_000_000)

    # Duration to run stimulation (in seconds)
    STIMULATION_TIME = 5

    # Output directory for logging
    OUTPUT_FOLDER = "TI_dipole_logs"

    # ======================================================================
    # Helper Functions
    # ======================================================================

    def create_csv_logger(output_folder):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        filepath = os.path.join(output_folder, filename)
        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date-Time", "Channel", "Frequency (Hz)", "Amplitude (uA)"])
        return filepath

    def log_to_csv(filepath, channel, freq, amplitude):
        with open(filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), channel, freq, amplitude])

    def configure_channel(client, channel, amplitude_ua, phase_duration_us, interphase_delay_us, period_us):
        # Configure a single channel for stimulation
        client.send_command(f"set {channel}.stimenabled true")
        client.send_command(f"set {channel}.shape biphasic")
        client.send_command(f"set {channel}.polarity PositiveFirst")
        client.send_command(f"set {channel}.source KeyPressF1")  # Trigger source
        client.send_command(f"set {channel}.firstphasedurationmicroseconds {phase_duration_us}")
        client.send_command(f"set {channel}.secondphasedurationmicroseconds {phase_duration_us}")
        client.send_command(f"set {channel}.interphasedelaymicroseconds {interphase_delay_us}")
        client.send_command(f"set {channel}.firstphaseamplitudemicroamps {amplitude_ua}")
        client.send_command(f"set {channel}.secondphaseamplitudemicroamps {amplitude_ua}")

        # Set the number of stimulation pulses
        client.send_command(f"set {channel}.numberofstimpulses 255")

        # Set the pulse train period to achieve the desired frequency
        client.send_command(f"set {channel}.pulsetrainperiodmicroseconds {period_us}")

    # ======================================================================
    # Main Stimulation Routine
    # ======================================================================
    client = RHX_TCPClient(host=HOST, port=PORT)
    csv_file = create_csv_logger(OUTPUT_FOLDER)

    try:
        # Disable both channels first
        client.send_command(f"set {channel_a}.stimenabled false")
        client.send_command(f"set {channel_b}.stimenabled false")

        # Configure both channels
        configure_channel(client, channel_a, amplitude_ua1, PHASE_DURATION_US, INTERPHASE_DELAY_US, PERIOD_A_US)
        configure_channel(client, channel_b, amplitude_ua2, PHASE_DURATION_US, INTERPHASE_DELAY_US, PERIOD_B_US)

        # Upload parameters
        client.send_command("execute uploadstimparameters")

        # Log channel settings
        log_to_csv(csv_file, channel_a, FREQ_A, amplitude_ua1)
        log_to_csv(csv_file, channel_b, FREQ_B, amplitude_ua2)

        # Start running the system
        client.send_command("set runmode run")

        # Trigger both channels simultaneously
        client.send_command("execute manualstimtriggerpulse F1")

        print(f"Running TI dipole stimulation on {channel_a} and {channel_b} for {STIMULATION_TIME} s...")
        time.sleep(STIMULATION_TIME)

        # Stop the stimulation
        client.send_command("set runmode stop")

        # Disable the channels after stopping
        client.send_command(f"set {channel_a}.stimenabled false")
        client.send_command(f"set {channel_b}.stimenabled false")

        print("Stimulation stopped.")

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        client.close()
