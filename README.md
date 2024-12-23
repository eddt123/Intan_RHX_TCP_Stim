# Intan_RHX_TCP_Stim
Python scripts to send TCP commands to an Intan RHS system. 
The model recieves data from a 128 channel Open Ephys system and then will adjust the stimulation parameters to optimise the recording. 
This setup is being used to investigate selectivity of nerve stimulation. 

To make a TCP connection to the Intan RHS system press 'Network' and then select the remote TCP control. Ensure the port number aligns with the one in any of the script you are running below. Press 'connect' on the Intan and then run the below scripts to remotely control the Intan system. 

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

# Scripts
Choose the one you want to run for different stimulation paradigms. 

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

For each stimulation channel, each other channel is iteratively used as the return channel. This tests all avialable current paths. 

## TI_Intan_dipole.py
Used to do temporal interference using the Intan RHS system (PWM-TI). Creates a 1200Hz and 1250Hz pulse trains at two separate channels to create a interference region at 50Hz. The 50Hz region is created for ~0.2s (maximum number of pulses 255), equivalent to 10 period cycles for the 50Hz tone. 

## TI_Intan_dipole_cont.py
Identical to TI_Intan_dipole.py but uses a trigger to continously send a single pulse to make the 1200Hz and 1250Hz tone to allow for longer stimulation periods. 

## read.py
Connects to an Intan system and records data from channels which are specified. The recorded data is saved in the 'data' folder. Use the functions in the utils folder to display the data.  

## TI_dipole_algo
This contains a feedback loop between the 128 channels being recorded and the TI focal point. 
Different models (Bayesian Optimisation, Machine learning, Reinforcement Learning etc) can be selected as the base model to decide on actions.
The script uses a model which takes the 128 channels as an input then the channels for TI and the currents used for each TI channel are adjusted until the modulation index of the desired channel is maximised and the MI of the other channels is as small as it can be. 
