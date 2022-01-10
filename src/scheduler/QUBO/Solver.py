import scheduler.QUBO.macros as macros
from scheduler.Solver import Solver as GenericSolver
from models.Activity import Flight

class Solver(GenericSolver):
    def __init__(self, bqm=None, fixed_variables=None, aircraft=None, flights=None):
        return super().__init__(bqm, fixed_variables, aircraft, flights)
    
    def calculate_solution(self, sampler = macros.SAMPLER):
        return super().calculate_solution(sampler = sampler)
    
    def get_final_solution(self, sampler = macros.SAMPLER, to_print=True, print_matrix=False, export=False, modeltime=0):
        return super().get_final_solution(sampler = sampler, to_print=to_print, print_matrix=print_matrix, export=export, modeltime=modeltime, modulation='qubo')
    
    def get_energy_solution(self, sampler = macros.SAMPLER):
        return super().get_energy_solution(sampler = sampler, modulation='qubo')