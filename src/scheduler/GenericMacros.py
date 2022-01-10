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
SEATS_PARAM = 0.3
COST_PARAM = 0.3
DEBUG=False
MAINTENANCE_TYPES = ['A','B','C','3C','D']
INITIAL_DATETIME = "01/09/2009 00:00"
FINAL_DATETIME = "02/09/2009 00:00"
#WINDOW_SLIDING_HOURS = 12
#WINDOW_SIZE = 24