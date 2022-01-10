from abc import ABC
import scheduler.GenericMacros as macros
from models.Activity import Flight, Maintenance
from scheduler.Solution import Solution
from dwave.system import DWaveSampler, EmbeddingComposite
import dwave.inspector
from dwave.system import LeapHybridSampler
from hybrid.reference import KerberosSampler
from neal import SimulatedAnnealingSampler
from tabu import TabuSampler
from dimod.reference.samplers import ExactSolver
import dwave.inspector
from copy import deepcopy
import timeit

class Solver(ABC):

    def __init__(self, bqm=None, fixed_variables=None, aircraft=None, flights=None):
        self.bqm = bqm
        self.fixed_variables = fixed_variables
        self.aircraft = aircraft
        self.flights = flights

    def get_all_solution(self, sampler = None, modulation=None):
        
        all_solutions = self.calculate_all_solution(sampler)
        for index, sol in enumerate(all_solutions):
            solution = sol['solution']
            energy = sol['energy']
            solution_obj = Solution(self.flights, self.aircraft, solution, solving_time = -1, bqm = self.bqm, fixed_var = self.fixed_variables, energy = energy, sampler=sampler, modulation=modulation)
            verify, message, seats, cost, flights_cost = solution_obj.message_verify()
            all_solutions[index]['valid'] = verify
            all_solutions[index]['seats'] = seats
            all_solutions[index]['cost'] = cost
            all_solutions[index]['flights_cost'] = flights_cost
            if not verify:
                all_solutions[index]['message'] = message
        return all_solutions
    
    def get_solution(self, sampler = None, modulation=None):
        
        solution, solving_time, energy = self.calculate_solution(sampler)
        if solution is None:
            return None, None
        solution_obj = Solution(self.flights, self.aircraft, solution, solving_time = solving_time, bqm = self.bqm, fixed_var = self.fixed_variables, energy = energy, sampler=sampler, modulation=modulation)
        return solution_obj.verify_relaxed(), solution_obj

    def get_final_solution(self, sampler = None, to_print=True, print_matrix=False, export=False, modeltime=0, modulation=None):

        valid, solution = self.get_solution(sampler, modulation)
        if solution is None:
            print("No solution")
            return None
        if macros.DEBUG:
            if print_matrix:
                solution.print_matrix(modeltime)
            else:
                solution.print_list(modeltime)
            if valid:
                print("Works")        
            else:
                print("No valid solution")
        else:
            if valid:
                if export:
                    solution.print_export(self.flights, print_matrix, modeltime)
                else:
                    if to_print:
                        if print_matrix:
                            solution.print_matrix(modeltime)
                        else:
                            solution.print_list(modeltime)
                print("works")
            else:
                print("No valid solution")
        return solution
    
    def get_energy_solution(self, sampler = None, modulation=None):
        all_solutions = self.get_all_solution(sampler, modulation)
        table = "  Energy    |   Valid   |   Message  |  Free Seats  |  Cost  |  Flights Cost  |\n"
        for solution in all_solutions:
            if not solution['valid']:
                table += str(solution['energy']) + " | " + str(solution['valid']) + " | "+ str(solution['message']) + " | "+str(solution['seats']) +" | "+str(solution['cost']) + " | "+ str(solution['flights_cost']) +"\n"
            else:
                table += str(solution['energy']) + " | " + str(solution['valid']) + " |     |"+str(solution['seats']) +" | "+str(solution['cost']) +" | "+ str(solution['flights_cost']) +"\n"
        print(table)
        
    def calculate_solution(self, sampler = None):

        initialtime = timeit.default_timer()

        if self.bqm is None:
            return None, None
        solution = [[] for i in range(len(self.aircraft))] # matrix: rows -> aircraft;  columns -> flights that are operated by each aircraft
        
        if sampler is None:
            sampler = macros.SAMPLER

        if sampler == macros.Samplers.LEAP_HYBRID:

            samplerobj = LeapHybridSampler()
            results = samplerobj.sample(self.bqm)

            # smpl = {'0,1': 1.0, '1,3': 0.0, '1,3,4,3,and': 0.0, '1,4': 1.0, '1,4,4,4,and': 0.0, '2,3': 1.0, '2,3,4,3,and': 1.0, '2,4': 0.0, '2,4,4,4,and': 0.0, '3,3': 1.0, '3,4': 0.0, '4,3': 1.0, '4,4': 0.0, '6,1': 0.0}

        if sampler == macros.Samplers.KERBEROS:
            
            samplerobj = KerberosSampler()
            results = samplerobj.sample(self.bqm, max_iter = 20)

            # smpl = {'0,1': 1.0, '1,3': 0.0, '1,3,4,3,and': 0.0, '1,4': 1.0, '1,4,4,4,and': 0.0, '2,3': 1.0, '2,3,4,3,and': 1.0, '2,4': 0.0, '2,4,4,4,and': 0.0, '3,3': 1.0, '3,4': 0.0, '4,3': 1.0, '4,4': 0.0, '6,1': 0.0}

        
        if sampler == macros.Samplers.EXACT_SOLVER:

            samplerobj = ExactSolver()
            results = samplerobj.sample(self.bqm)
        
        if sampler == macros.Samplers.SIMULATED_ANNEALING:

            samplerobj = SimulatedAnnealingSampler()
            results = samplerobj.sample(self.bqm, num_reads=500, chain_strength=1000)

            #dwave.inspector.show(results)

            #print(results)
        
        if sampler == macros.Samplers.TABU_SEARCH:

            samplerobj = TabuSampler()
            results = samplerobj.sample(self.bqm)
        
        if sampler == macros.Samplers.QUANTUM:

            samplerobj = EmbeddingComposite(DWaveSampler())
            results = samplerobj.sample(self.bqm, num_reads = 100, chain_strength=2*max(max(self.bqm.linear.values()), max(self.bqm.quadratic.values())))
            try:
                print(results)
            except:
                pass
            print(results.info)
            dwave.inspector.show(results)


        #smpl, energy = next(iter(results.data(['sample', 'energy'])))
        
        energy = None
        if len(results) > 0:
            smpl = results.first.sample
            energy = results.first.energy

            for index in smpl:
                if smpl[index] == 1.0:
                    elems = index.split(',')
                    if len(elems) == 2:
                        solution[int(elems[1])].append(int(elems[0]))
        for fixed in self.fixed_variables:
            elems = fixed.split(',')
            if len(elems) == 2:
                solution[int(elems[1])].append(int(elems[0]))


        finaltime = timeit.default_timer() - initialtime       

        print(solution) 

        return solution, finaltime, energy


    def calculate_all_solution(self, sampler = None):

        initialtime = timeit.default_timer()

        if self.bqm is None:
            return None, None
        all_solutions = []
        solution = [[] for i in range(len(self.aircraft))] # matrix: rows -> aircraft;  columns -> flights that are operated by each aircraft
        
        if sampler is None:
            sampler = macros.SAMPLER

        if sampler == macros.Samplers.LEAP_HYBRID:

            samplerobj = LeapHybridSampler()
            results = samplerobj.sample(self.bqm)

            # smpl = {'0,1': 1.0, '1,3': 0.0, '1,3,4,3,and': 0.0, '1,4': 1.0, '1,4,4,4,and': 0.0, '2,3': 1.0, '2,3,4,3,and': 1.0, '2,4': 0.0, '2,4,4,4,and': 0.0, '3,3': 1.0, '3,4': 0.0, '4,3': 1.0, '4,4': 0.0, '6,1': 0.0}

        if sampler == macros.Samplers.KERBEROS:
            
            samplerobj = KerberosSampler()
            results = samplerobj.sample(self.bqm, max_iter = 20)

            # smpl = {'0,1': 1.0, '1,3': 0.0, '1,3,4,3,and': 0.0, '1,4': 1.0, '1,4,4,4,and': 0.0, '2,3': 1.0, '2,3,4,3,and': 1.0, '2,4': 0.0, '2,4,4,4,and': 0.0, '3,3': 1.0, '3,4': 0.0, '4,3': 1.0, '4,4': 0.0, '6,1': 0.0}

        
        if sampler == macros.Samplers.EXACT_SOLVER:

            samplerobj = ExactSolver()
            results = samplerobj.sample(self.bqm)
        
        if sampler == macros.Samplers.SIMULATED_ANNEALING:

            samplerobj = SimulatedAnnealingSampler()
            results = samplerobj.sample(self.bqm, num_reads=500, chain_strength=2*max(max(self.bqm.linear.values()), max(self.bqm.quadratic.values())))

            #dwave.inspector.show(results)

            #print(results)
        
        if sampler == macros.Samplers.TABU_SEARCH:

            samplerobj = TabuSampler()
            results = samplerobj.sample(self.bqm)
        
        if sampler == macros.Samplers.QUANTUM:

            samplerobj = EmbeddingComposite(DWaveSampler())
            results = samplerobj.sample(self.bqm, num_reads = 100, chain_strength=2*max(max(self.bqm.linear.values()), max(self.bqm.quadratic.values())))
            try:
                print(results)
            except:
                pass
            print(results.info)
            dwave.inspector.show(results)

        if len(results) > 0:
            for i in results.data(['sample','energy']):
                solution = [[] for i in range(len(self.aircraft))] # matrix: rows -> aircraft;  columns -> flights that are operated by each aircraft
                smpl, energy = i
                for index in smpl:
                    if smpl[index] == 1.0:
                        elems = index.split(',')
                        if len(elems) == 2:
                            solution[int(elems[1])].append(int(elems[0]))
                for fixed in self.fixed_variables:
                    elems = fixed.split(',')
                    if len(elems) == 2:
                        solution[int(elems[1])].append(int(elems[0]))
                all_solutions.append({'solution': deepcopy(solution), 'energy':energy})

        return all_solutions

    
