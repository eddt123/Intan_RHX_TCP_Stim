import time
from utils.TI import run_ti_dipole_stimulation

# ======================================================================
# Input Arguments
# ======================================================================

# Channels for stimulation
channel_a = "a-000"  # Source for dipole A
channel_b = "a-001"  # Source for dipole B
return_channel_a = "a-002"  # Return for dipole A
return_channel_b = "a-003"  # Return for dipole B

# Stimulation amplitudes in microamps
amplitude_ua1 = 100  # Amplitude for channel_a
amplitude_ua2 = 100  # Amplitude for channel_b

# ======================================================================
# Run the Stimulation
# ======================================================================

try:
    print("Starting TI dipole stimulation...")
    print(f"Source A: {channel_a}, Source B: {channel_b}")
    print(f"Sink A: {return_channel_a}, Sink B: {return_channel_b}")

    # Call the imported function with the defined arguments
    run_ti_dipole_stimulation(
        channel_a=channel_a,
        channel_b=channel_b,
        return_channel_a=return_channel_a,
        return_channel_b=return_channel_b,
        amplitude_ua1=amplitude_ua1,
        amplitude_ua2=amplitude_ua2
    )

except KeyboardInterrupt:
    print("Process interrupted by user.")
finally:
    print("Exiting program.")
