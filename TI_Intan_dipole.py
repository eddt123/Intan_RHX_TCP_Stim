import time
import os
from datetime import datetime
import csv

from TCP import RHX_TCPClient

# ======================================================================
# Configuration Parameters
# ======================================================================
HOST = "127.0.0.1"
PORT = 5000

CHANNEL_A = "a-000"
CHANNEL_B = "a-001"

# Pulse amplitudes in microamps (adjust as needed)
AMPLITUDE_UA1 = 100
AMPLITUDE_UA2 = 100 

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
STIMULATION_TIME = 10

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

    # This is the maximum number of pulses, only leads to 0.2s of stim = ~10 periods of 50Hz pulse
    client.send_command(f"set {channel}.numberofstimpulses 255")

    # Set the pulse train period to achieve the desired frequency
    client.send_command(f"set {channel}.pulsetrainperiodmicroseconds {period_us}")

if __name__ == "__main__":
    # Connect to the Intan system
    client = RHX_TCPClient(host=HOST, port=PORT)
    csv_file = create_csv_logger(OUTPUT_FOLDER)

    try:
        # Disable both channels first
        client.send_command(f"set {CHANNEL_A}.stimenabled false")
        client.send_command(f"set {CHANNEL_B}.stimenabled false")

        # Configure both channels
        configure_channel(client, CHANNEL_A, AMPLITUDE_UA1, PHASE_DURATION_US, INTERPHASE_DELAY_US, PERIOD_A_US)
        configure_channel(client, CHANNEL_B, AMPLITUDE_UA2, PHASE_DURATION_US, INTERPHASE_DELAY_US, PERIOD_B_US)

        # Upload parameters
        client.send_command("execute uploadstimparameters")

        # Log channel settings
        log_to_csv(csv_file, CHANNEL_A, FREQ_A, AMPLITUDE_UA1)
        log_to_csv(csv_file, CHANNEL_B, FREQ_B, AMPLITUDE_UA2)

        # Start running the system
        client.send_command("set runmode run")

        # Trigger both channels simultaneously
        client.send_command("execute manualstimtriggerpulse F1")

        print(f"Running TI dipole stimulation at {FREQ_A} Hz and {FREQ_B} Hz for {STIMULATION_TIME} s...")
        time.sleep(STIMULATION_TIME)

        # Stop the stimulation
        client.send_command("set runmode stop")

        # Disable the channels after stopping
        client.send_command(f"set {CHANNEL_A}.stimenabled false")
        client.send_command(f"set {CHANNEL_B}.stimenabled false")

        print("Stimulation stopped.")

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        client.close()
