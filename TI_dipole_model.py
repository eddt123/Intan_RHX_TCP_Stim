import time
import numpy as np
from utils.TI import run_ti_dipole_stimulation
from models.bo_model import BOModel

from utils.read_data import read_intan_rhs_file

# ----------------------------------------------------------------------
# Configuration / Parameters
# ----------------------------------------------------------------------
# Available TI channels: a00 through a011 (e.g., "a-000", "a-001", ..., "a-011")
TI_CHANNELS = [f"a-0{str(i).zfill(2)}" for i in range(12)]

# We assume we have 128 recording channels (e.g., "r-000", "r-001", ..., "r-127")
RECORDING_CHANNELS = [f"r-{str(i).zfill(3)}" for i in range(128)]

# Amplitude range in microamps
AMPLITUDE_RANGE = (0, 200)

# Placeholder for how frequently we update the stimulation (in seconds)
LOOP_INTERVAL = 5

# Number of iterations to run the optimization loop
MAX_ITERATIONS = 20

# Target recording channel to maximize signal on (example: channel 30)
TARGET_CHANNEL_INDEX = 30

# ----------------------------------------------------------------------
# Data Acquisition
# ----------------------------------------------------------------------

def get_recording_data():
    """
    Acquire and process data from (up to) 128 recording channels
    of an Intan .rhs file.

    Returns
    -------
    np.ndarray
        A 1D numpy array of length 128 representing some processed 
        measurement on each recording channel. In this example, we 
        simply take the 'last sample' from each channel as a placeholder.
    """
    # 1) NEED TO CHANGE THIS SO THAT THE RECORDING FUNCTION WE CAN SPECIFY THE OUTPUT
    file_path = r"C:\Users\eddyt\Documents\Intan recordings\testing\testing2_250102_174724\testing2_250102_174724.rhs"

    # 2) Use the utility function to read the file and extract amplifier data.
    data, header = read_intan_rhs_file(file_path)
    amplifier_data = data['amplifier_data']  # shape: (num_channels, total_samples)

    # 3) Perform any further signal processing as desired.
    #    For now, we just grab the last sample from the first 128 channels.
    num_channels_in_file = amplifier_data.shape[0]
    if num_channels_in_file >= 128:
        # Example: last sample from each channel
        recording_data = amplifier_data[:128, -1]
    else:
        # Fallback if fewer than 128 channels exist in the file
        # (Or handle differently if your system always has at least 128)
        dummy_fill = 128 - num_channels_in_file
        recording_data = np.concatenate([
            amplifier_data[:, -1],  # actual channels
            np.zeros(dummy_fill)    # zero pad
        ])

    # Return our 1D array of length 128
    return recording_data

# ----------------------------------------------------------------------
# Main Optimization Script
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Initialize the Bayesian Optimization model
    model = BOModel(ti_channels=TI_CHANNELS, amplitude_range=AMPLITUDE_RANGE)

    for iteration in range(MAX_ITERATIONS):
        print(f"Iteration {iteration + 1}/{MAX_ITERATIONS}")

        # Get suggested parameters
        action = model.suggest_parameters()
        channel_a = action["channel_a"]
        channel_b = action["channel_b"]
        return_channel_a = action["return_channel_a"]
        return_channel_b = action["return_channel_b"]
        amplitude_a = action["amplitude_a"]
        amplitude_b = action["amplitude_b"]

        print(f"Selected parameters: "
              f"channel_a={channel_a}, channel_b={channel_b}, "
              f"return_channel_a={return_channel_a}, return_channel_b={return_channel_b}, "
              f"amplitude_a={amplitude_a}, amplitude_b={amplitude_b}")

        # Run stimulation with both source and return channels
        run_ti_dipole_stimulation(
            channel_a,
            channel_b,
            return_channel_a,
            return_channel_b,
            amplitude_a,
            amplitude_b
        )

        # Wait for stimulation to take effect
        time.sleep(LOOP_INTERVAL)

        # Acquire recording data
        recording_data = get_recording_data()

        # Compute a result metric for the optimizer
        result = (recording_data[TARGET_CHANNEL_INDEX]
                  - 0.1 * np.sum(np.delete(recording_data, TARGET_CHANNEL_INDEX)))

        print(f"Result for current configuration: {result}")

        # Update the Bayesian Optimization model with the new result
        model.update(action, result)

    # After loop, get the best result found
    best_result_value, best_params = model.best_result()
    print("Optimization complete.")
    print(f"Best parameters: {best_params}")
    print(f"Best result value: {best_result_value}")
