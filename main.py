import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/src")
import argparse
from Loader import read_data
from scheduler.Scheduler import Scheduler
from scheduler.Solution import Solution
from scheduler.CSP.SchedulerCSP import SchedulerCSP
from scheduler.QUBO.SchedulerQUBO import SchedulerQUBO
from scheduler.CSP.Solver import Solver as CSPSolver
from scheduler.QUBO.Solver import Solver as QUBOSolver
import json
import dimod
# from inital_solution.initial import DepthFirstAssign

def main():

    parser = argparse.ArgumentParser(description="""
    This script is going to create an efficient assignment for the Tail Assignment Problem 
    By default the problem is modeled as a BQM direclty using parameters for encouraging or disencouraging some assignments.
    The default formulation assumes that at least a valid situation exists (no extra flights are needed)
    """)
    parser.add_argument("--aircraftmodel", action='store_true', help="Do assignment considering a pre-assigned aircraft model instead of a pre-assigned aircraft fleet")
    parser.add_argument("--filesdirectory", default="data/final/model3", help="Path to the folder of the csv data files. Don't forget to follow the names' specifications")
    parser.add_argument("--printmatrix", action="store_true", help="Print solution as a matrix")
    parser.add_argument("--csp", action="store_true", help="Generate BQM using the Constraint Satisfaction Problem Library")
    parser.add_argument("--initialsolution", action="store_true", help="Use a pre-generated initial solution to be improved")
    parser.add_argument("--export", action="store_true", help="Export solution to a file")
    parser.add_argument("--generatedata", type=int, help="Number of flights to be generated")
    parser.add_argument("--energysolution", action="store_true", help="print solutions by energy")
    parser.add_argument("--groupdata", action="store_true", help="Get a solution trying to group data")
    parser.add_argument("--exportbqm", action="store_true", help="Calculate a bqm for the given problem and export it fot the files directory provided")
    parser.add_argument("--loadbqm", default=None, help="Path of the json file for the bqm to be calculated")


    args = parser.parse_args()
    if not args.loadbqm is None:
        with open(args.loadbqm) as json_file:
            bqm = json.load(json_file)
            if bqm["modeling"] is None or (bqm["modeling"] != 'QUBO' and bqm["modeling"] != 'CSP') or bqm["fixed_variables"] is None or type(bqm["fixed_variables"]) != list or bqm["modeling_time"] is None:
                
                raise ValueError("Parameters modeling ('CSP' or 'QUBO'), fixed_variables (list) and modeling_time (float) must be defined")
                return
            try:
                fixed_variables = bqm["fixed_variables"]
                modeling = bqm["modeling"]
                modeltime = float(bqm["modeling_time"])
                del bqm["fixed_variables"]
                del bqm["modeling"]
                del bqm["modeling_time"]
                bqm = dimod.BinaryQuadraticModel.from_serializable(bqm)
            except:
                raise ValueError("Parameters modeling ('CSP' or 'QUBO'), fixed_variables (list) and modeling_time (float) must be defined")
                return
            
            path = args.loadbqm.split("/")
            del path[-1]
            path = '/'.join(path)
            airports, aircraft_models, aircraft, flights, maintenances = read_data(args.aircraftmodel, path+"/", args.initialsolution, args.groupdata)


            if  modeling == "QUBO":
                solver = QUBOSolver(bqm, fixed_variables, aircraft, flights)
            elif modeling == "CSP":
                solver = CSPSolver(bqm, fixed_variables, aircraft, flights)
            
            if args.energysolution:
                solver.get_energy_solution()
            else:
                solver.get_final_solution(print_matrix=args.printmatrix, export=args.export, modeltime = modeltime)
            return


    if args.initialsolution:
        airports, aircraft_models, aircraft, flights, maintenances, initial_solution = read_data(args.aircraftmodel, args.filesdirectory+"/", args.initialsolution, args.groupdata)
       
        solution = Solution(aircraft = aircraft, flights = flights, solution = initial_solution)
    else:
        airports, aircraft_models, aircraft, flights, maintenances = read_data(args.aircraftmodel, args.filesdirectory+"/", args.initialsolution, args.groupdata)


    if args.csp:
        scheduler = SchedulerCSP(flights, aircraft, aircraft_models, args.aircraftmodel)
        if args.exportbqm:
            bqm, fixed_variables, finaltime = scheduler.get_bqm(args.filesdirectory)
        else:
            bqm, fixed_variables, finaltime = scheduler.get_bqm()
            solver = CSPSolver(bqm, fixed_variables, aircraft, flights)
            if args.energysolution:
                solver.get_energy_solution()
            else:
                solver.get_final_solution(print_matrix=args.printmatrix, export=args.export, modeltime = finaltime)
    
    else:
        scheduler = SchedulerQUBO(flights, aircraft, aircraft_models, args.aircraftmodel)
        if args.exportbqm:
            bqm, fixed_variables, finaltime = scheduler.get_bqm(args.filesdirectory)
        else:
            bqm, fixed_variables, finaltime = scheduler.get_bqm()
            solver = QUBOSolver(bqm, fixed_variables, aircraft, flights)
            if args.energysolution:
                solver.get_energy_solution()
            else:
                solver.get_final_solution(print_matrix=args.printmatrix, export=args.export, modeltime = finaltime)


if __name__ == "__main__":
    main()


