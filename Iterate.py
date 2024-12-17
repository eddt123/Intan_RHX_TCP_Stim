import socket
import time
import random
import csv
import os
from datetime import datetime

# Constants
CHANNEL_START = 0  # Start channel (e.g., a-000)
CHANNEL_END = 31   # End channel (e.g., a-031)
CURRENT_START = 33  # Start amplitude in microamps
CURRENT_END = 1000  # End amplitude in microamps
CURRENT_INCREMENT = 66  # Step size for current amplitude
DURATION_INCREMENT = 66  # Duration increment in microseconds
OUTPUT_FOLDER = "timing"
STIMULATION_TIME = 10 # how long in seconds the board is run with the stimulation parameters

# RHX TCP Client Class
class RHX_TCPClient:
    def __init__(self, host='127.0.0.1', port=5000, timeout=2):
        """Initialize TCP client and establish connection."""
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.connect()

    def connect(self):
        """Connect to the RHX TCP server."""
        try:
            self.sock.connect((self.host, self.port))
            print(f"Connected to RHX at {self.host}:{self.port}")
        except Exception as e:
            print(f"Connection error: {e}")
            self.sock = None

    def send_command(self, command, delay=0.1):
        """Send a command."""
        if self.sock:
            try:
                self.sock.sendall((command + "\n").encode('utf-8'))
                print(f"Sent: {command}")
                time.sleep(delay)
            except Exception as e:
                print(f"Error sending command: {e}")

    def close(self):
        """Close the connection."""
        if self.sock:
            self.sock.close()
            print("Connection closed.")

# Function to create CSV logger
def create_csv_logger(output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    filepath = os.path.join(output_folder, filename)
    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date-Time", "Channel", "Amplitude (uA)"])
    return filepath

# Function to log data to CSV
def log_to_csv(filepath, channel, amplitude):
    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), channel, amplitude])

if __name__ == "__main__":
    client = RHX_TCPClient(host="127.0.0.1", port=5000)
    csv_file = create_csv_logger(OUTPUT_FOLDER)

    # List of channels to iterate over
    channels = [f"a-{str(i).zfill(3)}" for i in range(CHANNEL_START, CHANNEL_END + 1)]

    # List of current values to iterate over
    current_values = list(range(CURRENT_START, CURRENT_END + 1, CURRENT_INCREMENT))

    previous_channel = None  # To keep track of the last active channel

    try:
        while current_values:
            # Randomly select a current value and remove it to avoid repetition
            current = random.choice(current_values)
            current_values.remove(current)

            # Randomly select a channel
            random.shuffle(channels)
            for channel in channels:
                print(f"Processing Channel: {channel}, Current: {current} µA")

                # Reset the previous channel
                if previous_channel:
                    client.send_command(f"set {previous_channel}.stimenabled false")

                # Configure the selected channel
                client.send_command(f"set {channel}.stimenabled true")
                client.send_command(f"set {channel}.shape biphasic")
                client.send_command(f"set {channel}.polarity PositiveFirst")
                client.send_command(f"set {channel}.firstphasedurationmicroseconds {DURATION_INCREMENT}")
                client.send_command(f"set {channel}.secondphasedurationmicroseconds {DURATION_INCREMENT}")
                client.send_command(f"set {channel}.interphasedelaymicroseconds 25")
                client.send_command(f"set {channel}.firstphaseamplitudemicroamps {current}")
                client.send_command(f"set {channel}.secondphaseamplitudemicroamps {current}")
                client.send_command(f"set {channel}.numberofstimpulses 5")
                client.send_command(f"set {channel}.pulsetrainperiodmicroseconds 10000")

                # Upload parameters and trigger stimulation
                client.send_command("execute uploadstimparameters")
                client.send_command("set runmode run")
                client.send_command(f"execute manualstimtriggerpulse {channel}")

                # Log the output to CSV
                log_to_csv(csv_file, channel, current)

                # Wait for stimulation duration
                time.sleep(STIMULATION_TIME)

                # Stop the board and set the current channel as previous
                client.send_command("set runmode stop")
                previous_channel = channel
                time.sleep(1)

    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        client.close()
