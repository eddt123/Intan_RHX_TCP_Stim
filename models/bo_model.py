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
        # Define the parameter space
        # channel_a: categorical
        # channel_b: categorical (same set as channel_a)
        # amplitude_a: integer
        # amplitude_b: integer
        self.ti_channels = ti_channels
        self.amplitude_range = amplitude_range

        self.space = [
            Categorical(ti_channels, name='channel_a'),
            Categorical(ti_channels, name='channel_b'),
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
        """
        # Suggest a new set of parameters from the optimizer
        suggestion = self.optimizer.ask()
        
        # Ensure channel_b != channel_a. If they are the same, re-sample until different.
        # This is a simple approach; a more elegant approach would encode pairs differently.
        while suggestion[1] == suggestion[0]:
            suggestion = self.optimizer.ask()
        
        channel_a, channel_b, amplitude_a, amplitude_b = suggestion
        
        return {
            "channel_a": channel_a,
            "channel_b": channel_b,
            "amplitude_a": amplitude_a,
            "amplitude_b": amplitude_b
        }

    def update(self, params, result):
        """
        Update the optimizer with the result from a given set of parameters.
        result should be a scalar score (the value you want to maximize).
        """
        # Convert to the parameter order used in suggest_parameters
        p = [params["channel_a"], params["channel_b"], params["amplitude_a"], params["amplitude_b"]]
        self.params_history.append(p)
        self.results_history.append(result)

        # The optimizer expects a MINIMIZATION problem, so if we want to maximize,
        # we can negate the result or tell the optimizer. 
        # skopt doesn't directly support maximizing, so we can just give it -result.
        self.optimizer.tell(p, -result)

    def best_result(self):
        """
        Return the best result found so far and corresponding parameters.
        """
        if not self.results_history:
            return None, None
        best_idx = np.argmax(self.results_history)
        return self.results_history[best_idx], self.params_history[best_idx]
