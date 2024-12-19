import socket
import time

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

    def send_command(self, command, delay=0.01):
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