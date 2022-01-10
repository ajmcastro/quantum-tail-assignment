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
OBJECTIVE_PARAM = 0.1
MAX_ONE_PARAM = 5
NO_OVERLAP_PARAM = 8.5
NO_PAIR_PARAM = 8.5
CONNECTIONS_PARAM = 1.3
CONNECTIONS_MAINTENANCE_PARAM = 0.65
CONNECTIONS_NO_MAINTENANCE_PARAM = 0.8
PATH_PARAM = 3
MAINTENANCES_PARAM = 4
SEATS_PARAM = 0.3
COST_PARAM = 0.3
WINDOW_SIZE = 30
DEBUG = True