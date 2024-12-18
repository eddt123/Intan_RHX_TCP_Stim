# Intan_RHX_TCP_Stim
A python script to send TCP commands to an Intan RHS system. 
The model recieves data from a 128 channel Open Ephys system and then will adjust the stimulation parameters to optimise the recording. 
This setup is being used to investigate selectivity of nerve stimulation. 


## Stimulation Commands

Set Stimulation Parameters:

    set a-001.shape Biphasic
    set a-001.polarity NegativeFirst
    set a-001.firstphasedurationmicroseconds 100
    set a-001.secondphasedurationmicroseconds 100
    set a-001.interphasedelaymicroseconds 50
    set a-001.firstphaseamplitudemicroamps 50
    set a-001.secondphaseamplitudemicroamps 50
    set a-001.numberofstimpulses 3
    set a-001.pulsetrainperiodmicroseconds 10000
    set a-001.stimenabled true

## Iterate.py
This script connects to the Intan RHX Command Server via TCP/IP to configure and trigger stimulation parameters on amplifier channels (a-000 to a-031, or a customizable range).

Key features:
    Random Channel Selection: Iterates randomly through the specified range of channels, ensuring only one channel is active at a time.
    Random Amplitude Values: Sets equal current values (first and second phase amplitudes) for stimulation, ranging from 33 µA to 1000 µA in customizable increments.
Channel Reset: 
    Automatically resets the previously active channel before enabling a new one.
CSV Logging: 
    Outputs a log file in a timing folder, recording the timestamp, channel, and current amplitude for each configuration.
    The script ensures that all channels and amplitudes are tested efficiently and sequentially while maintaining a clear log for analysis.