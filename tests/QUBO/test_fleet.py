import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")
import unittest
import scheduler.QUBO.macros as macros
from models.Activity import Activity, Flight, Maintenance
from models.AircraftModelFleet import AircraftModel
from models.Aircraft import Aircraft
from models.Airport import Airport
from models.CityPair import CityPair
from scheduler.QUBO.SchedulerQUBO import SchedulerQUBO
from scheduler.QUBO.Solver import Solver
from scheduler.Solution import Solution
from Loader import read_airports, read_aircraft_models, read_city_pairs, reorder_data

class TestSimpleTests(unittest.TestCase):
    
    def setUp(self):
        self.airports = read_airports("data/final/")
        self.aircraft_models = read_aircraft_models("data/final/")
        self.city_pairs = read_city_pairs(self.airports, "data/final/")
        self.sampler = macros.Samplers.EXACT_SOLVER
    
    def test_no_constraints(self):

        print("\n\n--------------------TEST NO CONSTRAINTS--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        self.assertTrue(valid)
        self.assertTrue([flight0] in solution.matrix)


    def test_no_overlap_flights(self):

        print("\n\n--------------------TEST NO OVERLAP FLIGHTS--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 04:40', '01/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0, flight1]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        print(bqm)

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        print(solution.matrix)

        self.assertTrue(valid)
        self.assertFalse([flight0,flight1] in solution.matrix)
        self.assertTrue([flight1] in solution.matrix or [flight0] in solution.matrix)
    
    def test_maximum_one_aircraft_per_flight(self):

        print("\n\n--------------------TEST MAXIMUM ONE AIRCRAFT PER FLIGHTS--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        aircraft1 = Aircraft(1, 'CSTTF', 'CALOUSTE GULBENKIAN', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)

        print(solution.matrix)
        
        self.assertTrue(valid)
        self.assertFalse([flight0] == solution.matrix[0] and [flight0] == solution.matrix[1])
    
    def test_impossible_pairs(self):

        print("\n\n--------------------TEST IMPOSSIBLE PAIRS--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 07:40', '01/09/2009 09:00', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0, flight1]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        self.assertTrue(valid)
        self.assertFalse([flight0,flight1] in solution.matrix)

    
    def test_possible_direct_pairs(self):

        print("\n\n--------------------TEST POSSIBLE DIRECT PAIRS--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,543,self.airports[self.airports.index('AMS')], self.airports[self.airports.index('LIS')], 'NB', '01/09/2009 07:40', '01/09/2009 09:00', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('AMS', 'LIS'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0, flight1]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        self.assertTrue(valid)
        self.assertTrue([flight0,flight1] in solution.matrix)
    
    def test_possible_undirected_pairs(self):

        print("\n\n--------------------TEST POSSIBLE UNDIRECT PAIRS--------------------\n\n")

        #Possible paths: LIS->AMS (0); AMS-> OPO (1); OPO->BCN
        #                LIS->AMS (0); AMS-> OPO (2); OPO->BCN
        #                LIS -> AMS (4)
        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('AMS')], self.airports[self.airports.index('OPO')], 'NB', '01/09/2009 07:40', '01/09/2009 09:00', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('AMS', 'OPO'))].distance, False)
        
        flight2 = Flight(2,2,542,self.airports[self.airports.index('AMS')], self.airports[self.airports.index('OPO')], 'NB', '01/09/2009 10:40', '01/09/2009 13:00', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('AMS', 'OPO'))].distance, False)

        flight3 = Flight(3,3,543,self.airports[self.airports.index('OPO')], self.airports[self.airports.index('BCN')], 'NB', '01/09/2009 21:00', '01/09/2009 22:40', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('OPO', 'BCN'))].distance, False)

        flight4 = Flight(4,4,544,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 23:30', '02/09/2009 01:40', 15, 113, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0, flight1, flight2, flight3, flight4]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        print(solution.matrix)

        self.assertTrue(valid)
        self.assertTrue([flight0,flight1,flight3] in solution.matrix or [flight0,flight2,flight3] in solution.matrix or [flight4] in solution.matrix)
        for sol in solution.matrix:
            if (flight0 in sol and flight3 in sol and not (flight1 in sol) and not (flight2 in sol)):
                self.assertFalse(True)  

    def test_enough_seats(self):

        print("\n\n--------------------TEST ENOUGH SEATS--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 133, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flights = [flight0]
        aircraft = [aircraft0]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()

        self.assertTrue(valid)
        self.assertFalse([flight0] in solution.matrix)
    
    def test_overlap_maintenances(self):

        print("\n\n--------------------TEST NO FLIGHT THAT OVERLAP MAINTENANCE--------------------\n\n")

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(1, 0, 'T2', '01/09/2009 06:00', '01/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

        flights = [flight0]
        aircraft = [aircraft0]
        maintenances = [maintenance0]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertFalse([flight0] in solution.matrix)
    
    def test_obligatory_flight_to_ensure_maintenance(self):

        print("\n\n--------------------TEST OBLIGATORY FLIGHT TO ENSURE MAINTENANCE--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)
        aircraft1 = Aircraft(1, 'CSTTF', 'CALOUSTE GULBENKIAN', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance1)

        flight0 = Flight(2,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'FNC'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]
        maintenances = [maintenance0, maintenance1]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertTrue(solution.matrix[0] == [maintenance0, flight0, maintenance1] and solution.matrix[1] == [])

    
    def test_no_path_flight_maintenance(self):

        print("\n\n--------------------TEST NO PATH MAINTENANCE AND FLIGHT--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)
        aircraft1 = Aircraft(1, 'CSTTF', 'CALOUSTE GULBENKIAN', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance1)

        flight0 = Flight(2,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'FNC'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]
        maintenances = [maintenance0, maintenance1]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertTrue(solution.matrix[0] == [maintenance0, maintenance1] and solution.matrix[1] == [flight0])

    def test_flight_that_is_able_to_connect_just_to_one_of_the_maintenances(self):

        print("\n\n--------------------TEST PROPER FLIGHT IS CHOSEN TO CONNECT MAINTENANCES--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

    
        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance1)


        flight0 = Flight(2,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'FNC'))].distance, False)

        flight1 = Flight(3,1,541,self.airports[self.airports.index('OPO')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('OPO', 'FNC'))].distance, False)

        flights = [flight0, flight1]
        aircraft = [aircraft0]
        maintenances = [maintenance0, maintenance1]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertTrue(solution.matrix[0] == [maintenance0, flight0, maintenance1])       

    def test_impossible_assignment_because_no_total_connection_between_maintenances(self):

        print("\n\n--------------------TEST ONLY IF TOTAL PATH EXISTS BETWEEN MAINTENANCES IT HAPPEND--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

    
        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance1)


        flight0 = Flight(2,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        flight1 = Flight(3,1,541,self.airports[self.airports.index('OPO')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('OPO', 'FNC'))].distance, False)

        flights = [flight0, flight1]
        aircraft = [aircraft0]
        maintenances = [maintenance0, maintenance1]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        #bqm, fixed_variables, _ = scheduler.get_bqm()
        self.assertRaises(NameError, scheduler.get_bqm)

        # solver = Solver(bqm, fixed_variables, aircraft, flights)
        # solution = solver.calculate_solution(self.sampler)
        # for elem in solution:
        #     elem.sort()
        
        # self.assertTrue(solver.verify_solution(solution))
        # self.assertTrue(solution[0] == [])

    def test_one_flight_to_ensure_maintenances_two_aircraft(self):

        print("\n\n--------------------TEST JUST ONE FLIGHT TO ENSURE MAINTENANCES OF 2 AIRCRAFT--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        aircraft1 = Aircraft(1, 'CSTTF', 'CALOUSTE GULBENKIAN', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)


        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 01:00', '01/09/2009 02:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft1.add_maintenance(maintenance1)

    
        maintenance2 = Maintenance(2, 2, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance2)

    
        maintenance3 = Maintenance(3, 3, 'T2', '01/09/2009 07:00', '01/09/2009 08:00', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft1.add_maintenance(maintenance3)

        flight0 = Flight(4,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'FNC'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]
        maintenances = [maintenance0, maintenance1, maintenance2, maintenance3]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        self.assertRaises(NameError, scheduler.get_bqm)
        # bqm, fixed_variables, _ = scheduler.get_bqm()

        # solver = Solver(bqm, fixed_variables, aircraft, flights)
        # solution = solver.calculate_solution(self.sampler)
        # print(solution)
        # for elem in solution:
        #     elem.sort()
        
        # self.assertTrue(solver.verify_solution(solution))
        # self.assertTrue((solution[0] == [0] and solution[1] == []) or (solution[0] == [] and solution[1] == [0]))
        

    def test_one_flight_to_connect_flights_and_maintenances_two_aircraft(self):
        
        print("\n\n--------------------TEST JUST ONE FLIGHT TO ENSURE CONNECTION BETWEEN FLIGHTS AND MAINTENANCES OF 2 AIRCRAFT--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        aircraft1 = Aircraft(1, 'CSTTF', 'CALOUSTE GULBENKIAN', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 22:00', '01/09/2009 23:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)


        maintenance1 = Maintenance(1, 1, 'T2', '01/09/2009 22:00', '01/09/2009 23:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft1.add_maintenance(maintenance1)


        flight0 = Flight(2,0,540,self.airports[self.airports.index('BCN')], self.airports[self.airports.index('OPO')], 'NB', '01/09/2009 02:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('BCN', 'OPO'))].distance, False)

        flight1 = Flight(3,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('OPO')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'OPO'))].distance, False)

        flight2 = Flight(4,2,542,self.airports[self.airports.index('OPO')], self.airports[self.airports.index('LIS')], 'NB', '01/09/2009 07:00', '01/09/2009 08:00', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('OPO', 'LIS'))].distance, False)

        flights = [flight0, flight1, flight2]
        aircraft = [aircraft0, aircraft1]
        maintenances = [maintenance0, maintenance1]

        reorder_data(flights, maintenances)

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        print(solution.matrix)

        self.assertTrue(valid)
        self.assertTrue((solution.matrix[0] == [flight0, flight2, maintenance0] and solution.matrix[1] == [maintenance1]) or (solution.matrix[0] == [maintenance0] and solution.matrix[1] == [flight1,flight2, maintenance1]) or (solution.matrix[0] == [maintenance0] and solution.matrix[1] == [flight0,flight2, maintenance1]) or (solution.matrix[0] == [flight1,flight2, maintenance0] and solution.matrix[1] == [maintenance1]) or (solution.matrix[0] == [maintenance0] and solution.matrix[1] == [flight2, maintenance1]) or (solution.matrix[0] == [flight2, maintenance0] and solution.matrix[1] == [maintenance1]) or (solution.matrix[0] == [flight1, maintenance0] and solution.matrix[1] == [flight0, flight2, maintenance1]))
        # self.assertTrue((solution.matrix[0] == [flight0, flight2, maintenance0] and solution.matrix[1] == [flight1, maintenance1]) or (solution.matrix[0] == [flight0, maintenance0] and solution.matrix[1] == [flight1,flight2, maintenance1]) or (solution.matrix[0] == [flight1, maintenance0] and solution.matrix[1] == [flight0,flight2, maintenance1]) or (solution.matrix[0] == [flight1,flight2, maintenance0] and solution.matrix[1] == [flight0, maintenance1]))

    
    def test_proper_fleet(self):

        print("\n\n--------------------TEST PROPER FLEET IS CHOSEN NO MATTER THE SEATS--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        aircraft1 = Aircraft(1, 'CSTOP', 'PEDRO NUNES', self.aircraft_models[self.aircraft_models.index('332')], 25, 244)

        flight0 = Flight(0,0,540,self.airports[self.airports.index('GIG')], self.airports[self.airports.index('LIS')], 'WB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('GIG', 'LIS'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertTrue(solution.matrix[0] == [] and solution.matrix[1] == [flight0])
    
    def test_bigger_fleet(self):

        print("\n\n--------------------TEST BIGGER FLEET IS CHOSEN--------------------\n\n")

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        aircraft1 = Aircraft(1, 'CSTOP', 'PEDRO NUNES', self.aircraft_models[self.aircraft_models.index('332')], 25, 244)

        flight0 = Flight(0,0,540,self.airports[self.airports.index('DKR')], self.airports[self.airports.index('LIS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 133, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('DKR', 'LIS'))].distance, False)

        flights = [flight0]
        aircraft = [aircraft0, aircraft1]

        scheduler = SchedulerQUBO(flights, aircraft, self.aircraft_models, False)
        bqm, fixed_variables, _ = scheduler.get_bqm()

        solver = Solver(bqm, fixed_variables, aircraft, flights)
        valid, solution = solver.get_solution(self.sampler)
        for elem in solution.matrix:
            elem.sort()
        
        self.assertTrue(valid)
        self.assertTrue(solution.matrix[0] == [] and solution.matrix[1] == [flight0])




if __name__ == "__main__":
    unittest.main()