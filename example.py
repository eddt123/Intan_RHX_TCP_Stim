from TCP import RHX_TCPClient

if __name__ == "__main__":
    client = RHX_TCPClient(host="127.0.0.1", port=5000)

    # Set stimulation parameters for Amplifier Channel 1 (a-001)
    client.send_command("set a-001.stimenabled true")
    client.send_command("set a-001.shape Triphasic")
    client.send_command("set a-001.polarity NegativeFirst")
    client.send_command("set a-001.firstphasedurationmicroseconds 100")
    client.send_command("set a-001.secondphasedurationmicroseconds 100")
    client.send_command("set a-001.interphasedelaymicroseconds 50")
    client.send_command("set a-001.firstphaseamplitudemicroamps 50")
    client.send_command("set a-001.secondphaseamplitudemicroamps 50")
    client.send_command("set a-001.numberofstimpulses 3")
    client.send_command("set a-001.pulsetrainperiodmicroseconds 10000")

    # Upload the stimulation parameters
    client.send_command("execute uploadstimparameters")

    # Trigger stimulation on channel 1
    client.send_command("execute manualstimtriggerpulse a-001")

    # Close the connection
    client.close()