'''
Bayesian optimisation:
Instead of randomly trying combinations or testing every possibility (like a brute-force approach), Bayesian Optimization uses past results to intelligently guess the next best combination to try.


Why BO?
It is well suited for tuning parameters when evaluations are expensive or noisy.
It uses a surrogate model (often a Gaussian Process, though other regressors can be used) to model the relationship between parameters and the observed outcome.
It then chooses new parameter sets to try in a way that balances exploring uncertain regions of the parameter space and exploiting regions that appear promising.

Alternatives:
Genetic Algorithms / Evolutionary Strategies: Could be used to evolve sets of parameters, but may require a large number of evaluations.
Reinforcement Learning (RL): Potentially overkill and requires framing the problem carefully as a repeated action/reward scenario.
Gradient-free optimization algorithms (e.g., Nelder-Mead, CMA-ES): Could work but may not handle the categorical nature (channel selection) as nicely.
Grid or Random Search: Very inefficient. You have a large discrete space (12 channels for channel_a, 11 possible distinct channels for channel_b, and a range of amplitudes).
'''

from skopt import Optimizer
from skopt.space import Categorical, Integer
import numpy as np

class BOModel:
    def __init__(self, ti_channels, amplitude_range=(0, 200)):
        # Define the parameter space:
        #   1) channel_a: categorical
        #   2) channel_b: categorical
        #   3) return_channel_a: categorical
        #   4) return_channel_b: categorical
        #   5) amplitude_a: integer
        #   6) amplitude_b: integer
        self.ti_channels = ti_channels
        self.amplitude_range = amplitude_range

        self.space = [
            Categorical(ti_channels, name='channel_a'),
            Categorical(ti_channels, name='channel_b'),
            Categorical(ti_channels, name='return_channel_a'),
            Categorical(ti_channels, name='return_channel_b'),
            Integer(amplitude_range[0], amplitude_range[1], name='amplitude_a'),
            Integer(amplitude_range[0], amplitude_range[1], name='amplitude_b')
        ]

        # Create a Bayesian optimization object
        self.optimizer = Optimizer(dimensions=self.space, random_state=0)

        # Keep track of (params, results)
        self.params_history = []
        self.results_history = []

    def suggest_parameters(self):
        """
        Suggest new parameters to try based on past results.
        Ensures channel_a, channel_b, return_channel_a, return_channel_b 
        are all distinct.
        """
        while True:
            # Suggest a new set of parameters from the optimizer
            suggestion = self.optimizer.ask()
            (channel_a, channel_b,
             return_channel_a, return_channel_b,
             amplitude_a, amplitude_b) = suggestion

            # Check uniqueness of all channels, we do not want to share any channels
            all_channels = {channel_a, channel_b, return_channel_a, return_channel_b}
            if len(all_channels) == 4:
                # We have four distinct channel names; break out of loop
                break
            # Otherwise, keep asking until we get a set of distinct channels

        return {
            "channel_a": channel_a,
            "channel_b": channel_b,
            "return_channel_a": return_channel_a,
            "return_channel_b": return_channel_b,
            "amplitude_a": amplitude_a,
            "amplitude_b": amplitude_b
        }

    def update(self, params, result):
        """
        Update the optimizer with the result from a given set of parameters.
        'result' should be a scalar score (the value you want to maximize).
        """
        # Convert to the parameter order used in suggest_parameters
        p = [
            params["channel_a"],
            params["channel_b"],
            params["return_channel_a"],
            params["return_channel_b"],
            params["amplitude_a"],
            params["amplitude_b"]
        ]
        self.params_history.append(p)
        self.results_history.append(result)

        # The optimizer expects a MINIMIZATION problem. We want to maximize,
        # so we pass -result.
        self.optimizer.tell(p, -result)

    def best_result(self):
        """
        Return the best result found so far and corresponding parameters.
        """
        if not self.results_history:
            return None, None
        best_idx = np.argmax(self.results_history)
        return self.results_history[best_idx], self.params_history[best_idx]

class TVBOModel:
    def __init__(self, ti_channels, amplitude_range=(0, 200), time_decay=0.9):
        """
        Initialize a Time-Varying Bayesian Optimization model.

        Parameters:
        - ti_channels: List of available channels for stimulation.
        - amplitude_range: Tuple (min, max) for amplitude values.
        - time_decay: Weight applied to past observations, with recent data having more influence.
        """
        self.ti_channels = ti_channels
        self.amplitude_range = amplitude_range
        self.time_decay = time_decay  # Determines how much old data influences the model.

        self.space = [
            Categorical(ti_channels, name='channel_a'),
            Categorical(ti_channels, name='channel_b'),
            Categorical(ti_channels, name='return_channel_a'),
            Categorical(ti_channels, name='return_channel_b'),
            Integer(amplitude_range[0], amplitude_range[1], name='amplitude_a'),
            Integer(amplitude_range[0], amplitude_range[1], name='amplitude_b')
        ]

        # Create a Bayesian optimization object
        self.optimizer = Optimizer(dimensions=self.space, random_state=0)

        # Keep track of (params, results, timestamps)
        self.params_history = []
        self.results_history = []
        self.time_stamps = []

    def suggest_parameters(self):
        """
        Suggest new parameters to try based on past results.
        Ensures channel_a, channel_b, return_channel_a, return_channel_b 
        are all distinct.
        """
        while True:
            suggestion = self.optimizer.ask()
            (channel_a, channel_b,
             return_channel_a, return_channel_b,
             amplitude_a, amplitude_b) = suggestion

            # Ensure all channels are distinct
            all_channels = {channel_a, channel_b, return_channel_a, return_channel_b}
            if len(all_channels) == 4:
                break

        return {
            "channel_a": channel_a,
            "channel_b": channel_b,
            "return_channel_a": return_channel_a,
            "return_channel_b": return_channel_b,
            "amplitude_a": amplitude_a,
            "amplitude_b": amplitude_b
        }

    def update(self, params, result):
        """
        Update the optimizer with the result from a given set of parameters.
        Applies a time decay to older results to account for temporal changes.
        """
        # Convert to parameter order used in suggest_parameters
        p = [
            params["channel_a"],
            params["channel_b"],
            params["return_channel_a"],
            params["return_channel_b"],
            params["amplitude_a"],
            params["amplitude_b"]
        ]
        
        current_time = len(self.time_stamps)  # Simulate a time index (or use a real timestamp if available)
        self.params_history.append(p)
        self.results_history.append(result)
        self.time_stamps.append(current_time)

        # Apply time decay to past results
        adjusted_results = [
            -res * (self.time_decay ** (current_time - t)) 
            for t, res in enumerate(self.results_history)
        ]

        # Update optimizer with decayed results
        for param, adj_result in zip(self.params_history, adjusted_results):
            self.optimizer.tell(param, adj_result)

    def best_result(self):
        """
        Return the best result found so far and corresponding parameters.
        """
        if not self.results_history:
            return None, None
        best_idx = np.argmax(self.results_history)
        return self.results_history[best_idx], self.params_history[best_idx]