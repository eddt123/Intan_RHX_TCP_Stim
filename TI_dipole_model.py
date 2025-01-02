import time
import numpy as np
from utils.TI import run_ti_dipole_stimulation
from models.bo_model import BOModel

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
    Placeholder function to acquire data from 128 recording channels.
    Need to change this to be for the 128 channels of the Intan. 

    Returns
    -------
    np.ndarray
        A mock 1D numpy array of length 128 representing the current amplitude 
        or measured value on each recording channel.
    """
    # Replace this with the real implementation
    # change this to calculate the Modulation Index for each channel
    # filter out anything but the tone
    # see the signal processing part of octopole paper

    # use the read_data method of using the .recording class
    # then use the read function to actually read this .rhs file to extract all the channel values
    # also this script we need to specify where the data can be found
    return np.random.rand(128)

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
