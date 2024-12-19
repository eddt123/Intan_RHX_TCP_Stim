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

AMPLITUDE_UA = 100
PHASE_DURATION_US = 100
INTERPHASE_DELAY_US = 0

FREQ_A = 1200  # Hz
FREQ_B = 1250  # Hz

# Period in seconds based on frequency
PERIOD_A = 1.0 / FREQ_A   # ~0.0008333 s
PERIOD_B = 1.0 / FREQ_B   # 0.0008 s

STIMULATION_TIME = 0.2  # Run for 0.2 seconds (for example)

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

def configure_channel(client, channel, amplitude_ua, phase_duration_us, interphase_delay_us):
    # Configure a single channel for one pulse per trigger
    client.send_command(f"set {channel}.stimenabled true")
    client.send_command(f"set {channel}.shape biphasic")
    client.send_command(f"set {channel}.polarity PositiveFirst")
    client.send_command(f"set {channel}.firstphasedurationmicroseconds {phase_duration_us}")
    client.send_command(f"set {channel}.secondphasedurationmicroseconds {phase_duration_us}")
    client.send_command(f"set {channel}.interphasedelaymicroseconds {interphase_delay_us}")
    client.send_command(f"set {channel}.firstphaseamplitudemicroamps {amplitude_ua}")
    client.send_command(f"set {channel}.secondphaseamplitudemicroamps {amplitude_ua}")
    # Only one pulse per trigger press
    client.send_command(f"set {channel}.numberofstimpulses 1")

if __name__ == "__main__":
    # Connect to the Intan system
    client = RHX_TCPClient(host=HOST, port=PORT)
    csv_file = create_csv_logger(OUTPUT_FOLDER)

    try:
        # Disable both channels first
        client.send_command(f"set {CHANNEL_A}.stimenabled false")
        client.send_command(f"set {CHANNEL_B}.stimenabled false")

        # Configure both channels
        configure_channel(client, CHANNEL_A, AMPLITUDE_UA, PHASE_DURATION_US, INTERPHASE_DELAY_US)
        configure_channel(client, CHANNEL_B, AMPLITUDE_UA, PHASE_DURATION_US, INTERPHASE_DELAY_US)

        # Assign different trigger sources for each channel
        client.send_command(f"set {CHANNEL_A}.source KeyPressF1")
        client.send_command(f"set {CHANNEL_B}.source KeyPressF2")

        # Upload parameters
        client.send_command("execute uploadstimparameters")

        # Log channel settings
        log_to_csv(csv_file, CHANNEL_A, FREQ_A, AMPLITUDE_UA)
        log_to_csv(csv_file, CHANNEL_B, FREQ_B, AMPLITUDE_UA)

        # Start running mode
        client.send_command("set runmode run")

        # Current time reference
        start_time = time.time()
        next_A = start_time
        next_B = start_time

        # Loop for the designated stimulation time
        while time.time() - start_time < STIMULATION_TIME:
            now = time.time()

            # Check if it's time to trigger channel A (F1)
            if now >= next_A:
                client.send_command("execute manualstimtriggerpulse F1")
                next_A += PERIOD_A

            # Check if it's time to trigger channel B (F2)
            if now >= next_B:
                client.send_command("execute manualstimtriggerpulse F2")
                next_B += PERIOD_B

            # Short sleep to reduce busy waiting (adjust as needed)
            time.sleep(1e-4)  # 100 µs sleep

        # Stop stimulation
        client.send_command("set runmode stop")
        client.send_command(f"set {CHANNEL_A}.stimenabled false")
        client.send_command(f"set {CHANNEL_B}.stimenabled false")

        print("Stimulation stopped.")

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        client.close()
