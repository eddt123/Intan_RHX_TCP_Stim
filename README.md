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
