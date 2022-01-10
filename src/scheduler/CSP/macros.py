from enum import Enum

class Samplers(Enum):
    LEAP_HYBRID = 1
    KERBEROS = 2
    EXACT_SOLVER = 3
    SIMULATED_ANNEALING = 4
    TABU_SEARCH = 5
    QUANTUM = 6

    def __eq__(self, other):
        return self.value == other.value

SAMPLER = Samplers.SIMULATED_ANNEALING
MIN_ROTATION_TIME = 40
MAXIMUM_COST = 11674698.216493046
#WINDOW_SIZE = 30
OBJECTIVE_PARAM = 0.1
SEATS_PARAM = 0.3
COST_PARAM = 0.3
DEBUG=False