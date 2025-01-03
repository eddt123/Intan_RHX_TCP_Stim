'''
example script on how to use the recording function in the TCP class
'''

from TCP import RHX_TCPClient

# Initialize the client (commands server)
client = RHX_TCPClient(host='127.0.0.1', port=5000)

# Perform the recording (for 10 seconds, data directory "data/")
# Data enabling and run control is handled inside the recording method.
client.recording(record_time=10, base_directory=r"C:\Users\eddyt\Documents\Intan recordings")

# Close the connection
client.close()
