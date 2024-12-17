import socket

class RHX_TCPClient:
    def __init__(self, host='127.0.0.1', port=5000):
        """
        Initializes the TCP client and establishes a connection.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        """Establishes the connection to the RHX command server."""
        try:
            self.sock.connect((self.host, self.port))
            print(f"Connected to RHX at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.sock = None

    def send_command(self, command):
        """Sends a command over the existing connection."""
        if self.sock:
            try:
                self.sock.sendall(command.encode('utf-8'))
                response = self.sock.recv(1024).decode('utf-8')
                print(f"Sent: {command}\nResponse: {response}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def close(self):
        """Closes the connection."""
        if self.sock:
            self.sock.close()
            print("Connection closed.")

# Example usage:
if __name__ == "__main__":
    client = RHX_TCPClient(host="127.0.0.1", port=5000) # change this for the correct host and port once intan rhs is connected

    # Example: Set stimulation parameters for channel 1
    client.send_command("set stimparameters.channel-1.amplitude_microamps 50")
    client.send_command("set stimparameters.channel-1.duration_milliseconds 100")
    client.send_command("set stimparameters.channel-1.frequency_hz 10")
    
    # Upload the stimulation parameters
    client.send_command("execute uploadstimparameters")
    
    # Optionally trigger stimulation on channel 1
    client.send_command("execute manualstimtriggerpulse channel-1")

    client.close()
