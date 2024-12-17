import socket
import time  # Import time for adding delays

class RHX_TCPClient:
    def __init__(self, host='127.0.0.1', port=5000, timeout=2):
        """Initialize TCP client and establish connection."""
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)  # Set socket timeout for connection
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
        """Send a command without waiting for a response."""
        if self.sock:
            try:
                self.sock.sendall(command.encode('utf-8'))  # Send the command
                print(f"Sent: {command}")
                time.sleep(delay)  # Add a small delay to ensure processing
            except Exception as e:
                print(f"Error sending command: {e}")

    def close(self):
        """Close the connection."""
        if self.sock:
            self.sock.close()
            print("Connection closed.")

if __name__ == "__main__":
    client = RHX_TCPClient(host="127.0.0.1", port=5000)

    # Set stimulation parameters for Amplifier Channel 1 (a-001)
    client.send_command("set a-001.stimenabled true")
    client.send_command("set a-001.shape biphasic")
    client.send_command("set a-001.polarity PositiveFirst")
    client.send_command("set a-001.firstphasedurationmicroseconds 200")
    client.send_command("set a-001.secondphasedurationmicroseconds 200")
    client.send_command("set a-001.interphasedelaymicroseconds 25")
    client.send_command("set a-001.firstphaseamplitudemicroamps 25")
    client.send_command("set a-001.secondphaseamplitudemicroamps 25")
    client.send_command("set a-001.numberofstimpulses 5")
    client.send_command("set a-001.pulsetrainperiodmicroseconds 10000")

    # Upload the stimulation parameters
    client.send_command("execute uploadstimparameters")



    client.send_command('set runmode run') # turn on the board
    client.send_command("execute manualstimtriggerpulse a-001") # starts the stimulation on that channel
    time.sleep(10)
    client.send_command('set runmode stop') # turn off the board, you cannot update stim parameters with the board still on


    # Close the connection
    client.close()
