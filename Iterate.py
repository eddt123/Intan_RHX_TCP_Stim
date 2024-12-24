import time
import random
import csv
import os
from datetime import datetime

from utils.TCP import RHX_TCPClient

# ----------------------------------------------------------------------
# Configuration / Parameters
# ----------------------------------------------------------------------
CHANNEL_START = 0   # Start channel (e.g., a-000)
CHANNEL_END = 11   # End channel (e.g., a-031)
CURRENT_START = 33  # Start amplitude in microamps
CURRENT_END = 1000  # End amplitude in microamps
CURRENT_INCREMENT = 66  # Step size for current amplitude
DURATION = 660      # Duration of the pulse in microseconds
OUTPUT_FOLDER = "timing"
STIMULATION_TIME = 10  # how long (in seconds) the board is run with these stim parameters


# ======================================================================
# Run the Stimulation
# ======================================================================

# Function to create CSV logger
def create_csv_logger(output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    filepath = os.path.join(output_folder, filename)
    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date-Time", "Main Channel", "Return Channel", "Amplitude (uA)"])
    return filepath

# Function to log data to CSV
def log_to_csv(filepath, main_channel, return_channel, amplitude):
    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            main_channel,
            return_channel,
            amplitude
        ])

if __name__ == "__main__":
    client = RHX_TCPClient(host="127.0.0.1", port=5000)
    csv_file = create_csv_logger(OUTPUT_FOLDER)

    # List of channels to iterate over
    channels = [f"a-{str(i).zfill(3)}" for i in range(CHANNEL_START, CHANNEL_END + 1)]

    # List of current values to iterate over (amplitudes)
    current_values = list(range(CURRENT_START, CURRENT_END + 1, CURRENT_INCREMENT))

    # Variables to keep track of previously enabled channels (so we can disable them)
    previous_main_channel = None
    previous_return_channel = None

    try:
        # We will keep picking amplitudes until we exhaust 'current_values'
        while current_values:
            # Randomly select an amplitude and remove it from the list
            amplitude = random.choice(current_values)
            current_values.remove(amplitude)

            # Now iterate through each channel in sequence
            for i in range(len(channels)):
                main_channel = channels[i]
                # Pick the "next" channel as the return channel (wrap around with modulo)
                return_channel = channels[(i + 1) % len(channels)]

                # Safety check: make sure we are not using the same channel
                if return_channel == main_channel:
                    # This should never happen with (i+1) % len(channels), but just in case
                    continue

                print(f"Processing Main: {main_channel}, Return: {return_channel}, "
                      f"Amplitude: {amplitude} µA")

                # Disable previously used channels before configuring new ones
                if previous_main_channel:
                    client.send_command(f"set {previous_main_channel}.stimenabled false")
                if previous_return_channel:
                    client.send_command(f"set {previous_return_channel}.stimenabled false")

                # -----------------------------
                # CONFIGURE MAIN (POSITIVE) CHANNEL
                # -----------------------------
                client.send_command(f"set {main_channel}.stimenabled true")
                client.send_command(f"set {main_channel}.shape monophasic")
                client.send_command(f"set {main_channel}.polarity PositiveFirst")
                client.send_command(f"set {main_channel}.source KeyPressF1")
                client.send_command(f"set {main_channel}.firstphasedurationmicroseconds {DURATION}")
                client.send_command(f"set {main_channel}.firstphaseamplitudemicroamps {amplitude}")
                client.send_command(f"set {main_channel}.numberofstimpulses 1")
                client.send_command(f"set {main_channel}.pulsetrainperiodmicroseconds 10000")

                # -----------------------------
                # CONFIGURE RETURN (NEGATIVE) CHANNEL
                # -----------------------------
                client.send_command(f"set {return_channel}.stimenabled true")
                client.send_command(f"set {return_channel}.shape monophasic")
                client.send_command(f"set {return_channel}.polarity NegativeFirst")
                client.send_command(f"set {return_channel}.source KeyPressF1")
                client.send_command(f"set {return_channel}.firstphasedurationmicroseconds {DURATION}")
                client.send_command(f"set {return_channel}.firstphaseamplitudemicroamps {amplitude}")
                client.send_command(f"set {return_channel}.numberofstimpulses 1")
                client.send_command(f"set {return_channel}.pulsetrainperiodmicroseconds 10000")

                # Upload parameters and run
                client.send_command("execute uploadstimparameters")
                client.send_command("set runmode run")

                # Trigger the pulses (acts as if F1 is being pressed)
                client.send_command("execute manualstimtriggerpulse F1")

                # Log the stimulation attempt
                log_to_csv(csv_file, main_channel, return_channel, amplitude)

                # Wait for the stimulation duration
                time.sleep(STIMULATION_TIME)

                # Stop the board
                client.send_command("set runmode stop")

                # Remember these so we can disable them on the next loop iteration
                previous_main_channel = main_channel
                previous_return_channel = return_channel

                # Short pause
                time.sleep(1)

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        # Disable any channels that might be left enabled
        if previous_main_channel:
            client.send_command(f"set {previous_main_channel}.stimenabled false")
        if previous_return_channel:
            client.send_command(f"set {previous_return_channel}.stimenabled false")
        client.close()
