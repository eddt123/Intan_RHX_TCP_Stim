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
        1. Stop board if running and set file save parameters.
        2. Clear all outputs (good practice).
        3. Enable desired channels for recording.
        4. Start recording (.rhs file).
        5. Wait for the specified record_time.
        6. Stop recording.
        
        The .rhs file should be saved in the specified path.
        """

        import datetime

        # 1. Stop board if it's currently running (so we can safely change file params)
        self.send_command("set runmode stop")
        time.sleep(0.2)

        # Generate a time-stamped subdirectory and filename
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        # e.g., base_directory="data", subdir="data/20250102_153025"
        data_dir = os.path.join(base_directory, date_str)
        os.makedirs(data_dir, exist_ok=True)
        print(f"Data directory created: {data_dir}")

        # 2. Clear all data outputs (good practice, especially if channels were previously enabled)
        self.send_command("execute clearalldataoutputs")
        time.sleep(0.2)

        # Set the path where Intan will save files
        cmd_path = f"set filename.path {data_dir}"
        self.send_command(cmd_path)
        time.sleep(0.2)

        # Set a base filename (without extension). Intan will append the timestamp internally as well.
        base_filename = f"recording_{date_str}"
        cmd_basefile = f"set filename.basefilename {base_filename}"
        self.send_command(cmd_basefile)
        time.sleep(0.2)

        # Tell Intan to automatically create a subfolder named with date/time (if you want)
        # If True, Intan will create an extra subfolder, so your final path might be nested further.
        self.send_command("set createnewdirectory true")
        time.sleep(0.2)

        # Choose to save everything into a single .rhs file
        self.send_command("set fileformat Traditional")
        time.sleep(0.2)

        # Optionally enable saving wideband amplifier waveforms
        self.send_command("set savewidebandamplifierwaveforms true")
        time.sleep(0.2)

        # 3. Enable recording for all amplifier channels a-000 through a-127
        #    Adjust if your system has a different number of channels or naming scheme.
        for i in range(128):
            channel_name = f"a-{i:03d}"
            self.send_command(f"set {channel_name}.recordingenabled true")
        time.sleep(0.2)

        # 4. Start recording (instead of just 'run' mode, we use 'record' to produce .rhs)
        self.send_command("set runmode record")
        print("Recording started...")
        
        # 5. Wait for the specified record_time (in seconds)
        time.sleep(record_time)

        # 6. Stop the recording
        self.send_command("set runmode stop")
        print("Recording stopped.")

        print("Recording completed. An .rhs file should be in the directory:")
        print(f"  {data_dir}")

