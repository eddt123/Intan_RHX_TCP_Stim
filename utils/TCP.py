import socket
import time
import os
import datetime

class RHX_TCPClient:
    def __init__(self, host='127.0.0.1', port=5000, timeout=2):
        """Initialize TCP client and establish connection to the commands server."""
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.connect()

    def connect(self):
        """Connect to the RHX TCP server (commands server)."""
        try:
            self.sock.connect((self.host, self.port))
            print(f"Connected to RHX at {self.host}:{self.port}")
        except Exception as e:
            print(f"Connection error: {e}")
            self.sock = None

    def send_command(self, command, delay=0.01):
        """Send a command without waiting for a response."""
        if self.sock:
            try:
                self.sock.sendall(command.encode('utf-8'))
                print(f"Sent: {command}")
                time.sleep(delay)
            except Exception as e:
                print(f"Error sending command: {e}")

    def close(self):
        """Close the connection."""
        if self.sock:
            self.sock.close()
            print("Connection closed.")

    def recording(self, record_time=10, base_directory="data"):
        """
        Perform a recording session:
          1. Clear all data outputs.
          2. Enable desired channels for TCP data output.
          3. Start the controller running.
          4. Wait for the specified record_time.
          5. Stop the controller.

        According to the documentation snippet, data will be output through the
        waveform/spike TCP servers if connected. This method just controls the controller 
        and what channels are outputting data.
        
        Note: The code does not attempt to connect to the waveform or spike output servers.
              This is just controlling the commands server as per the documentation.
        """

        # Create a timestamped directory (if you need a local directory structure)
        # The IntanRHX software configuration will determine where data is actually saved.
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        data_dir = os.path.join(base_directory, date_str)
        os.makedirs(data_dir, exist_ok=True)
        print(f"Data directory created: {data_dir}")

        # 1. Clear all data outputs
        self.send_command("execute clearalldataoutputs")

        # 2. Enable desired channels for TCP output
        # Example given in documentation:
        # write(tcommand, uint8('set a-008.tcpdataoutputenabledhigh true'));
        # write(tcommand, uint8('set analog-in-4.tcpdataoutputenabled true'));
        # Adjust these channels as needed. This is just an example.
    # Enable tcpdataoutputenabledhigh for a-000 through a-127
        for i in range(128):
            channel_name = f"a-{i:03d}"
            self.send_command(f"set {channel_name}.tcpdataoutputenabledhigh true")


        # 3. Start the controller running
        self.send_command("set runmode run")

        # 4. Record for record_time seconds
        time.sleep(record_time)

        # 5. Stop the controller
        self.send_command("set runmode stop")

        print("Recording completed.")
        print(f"Data output would have been streamed while running. Check your IntanRHX configuration for saved data.")
