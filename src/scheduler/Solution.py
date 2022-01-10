from models.Activity import Flight, Maintenance
from copy import deepcopy
import sys
import datetime
import pathlib
import statistics
import json

class Solution:
    def __init__(self, flights, aircraft, solution, is_complete=False, solving_time=0, bqm=None, fixed_var= None, energy = None, sampler=None, modulation=None):
        self.flights = flights
        self.aircraft = aircraft
        self.total_cost = 0
        self.nmb_free_seats = 0
        self.nmb_extra_flights_required = 0
        self.nmb_not_assigned_flights = 0
        if not is_complete:
            self.set_complete(solution)
        else:
            self.matrix = solution
        self.solving_time = solving_time
        self.bqm = bqm
        self.fixed_var = fixed_var
        self.energy = energy
        self.sampler = sampler
        self.modulation = modulation
        self.activities = []
    
    def set_complete(self, solution):
        """
        From a solution using local flight indexes get a complete solution with flight and maintenance objects

        Arguments:
            solution {list} -- marix with the indexes of the assigned flights 

        Returns:
            list -- matrix with the flights and maintenances for each aircraft already ordered
        """
        complete_matrix = []
        for aircraft_ref in self.aircraft:
            maintenances = aircraft_ref.maintenances
            flights_result = list(map(lambda flight_index: self.flights[flight_index], solution[aircraft_ref.index]))
            activities = [*maintenances, *flights_result]
            activities.sort()
            complete_matrix.append(activities)
        self.matrix = complete_matrix

    def print_matrix(self,  model_time = 0):

        if self.flights is None or self.aircraft is None:
            print("Not possible to print solution")
            return None

        if self.activities == []:
            self.get_activities()

        table_rows = [ ["              |" for j in range(len(self.activities)) ] for i in range(len(self.aircraft))]

        number_flights_per_aircraft_model = {}
        flight_minutes_per_aircraft_model = {}     
        for aircraft in self.aircraft:
            if not aircraft.model.model in number_flights_per_aircraft_model:
                number_flights_per_aircraft_model.update({aircraft.model.model: 0})
                flight_minutes_per_aircraft_model.update({aircraft.model.model: 0}) 
        for aircraft_index, solution_aircraft in enumerate(self.matrix):
            number_flights = 0
            number_flight_minutes = 0
            for solution_activity in solution_aircraft:
                if isinstance(solution_activity, Flight):
                    number_flights += 1
                    number_flight_minutes += solution_activity.activity_time
                table_rows[aircraft_index][self.activities.index(solution_activity)] = "       x      |"
            number_flights_per_aircraft_model[self.aircraft[aircraft_index].model.model] += number_flights
            flight_minutes_per_aircraft_model[self.aircraft[aircraft_index].model.model] += number_flight_minutes
        
        table = "\n      "

        for activity in self.activities:
            if isinstance(activity, Maintenance):
                table += "M:  " +activity.origin.iata_code + "->" + activity.destination.iata_code + " | "
            else:
                table += "F:  " +activity.origin.iata_code + "->" + activity.destination.iata_code + " | "
        table +="\n"
        rows = ""
        for index, aircraft_ref in enumerate(self.aircraft):
            rows += aircraft_ref.plate + ''.join(table_rows[index])+"\n"
        table += rows

        print(table)

        self.number_flights_per_aircraft_model = number_flights_per_aircraft_model
        #self.stdev_number_flights_per_aircraft_model = statistics.stdev(number_flights_per_aircraft)
        self.flight_minutes_per_aircraft_model = flight_minutes_per_aircraft_model
        #self.stdev_flight_minutes_per_aircraft = statistics.stdev(flight_minutes_per_aircraft)
        print("Number flights per aircraft: ", self.number_flights_per_aircraft_model)
        print("Number flight hours per aircraft: ", self.flight_minutes_per_aircraft_model)  
        print("Total cost: ", self.total_cost)
        print("Free seats: ", self.nmb_free_seats)
        print("Extra flights required: ", self.nmb_extra_flights_required)
        print("Not assigned flights: ", self.nmb_not_assigned_flights)


        print("\n\nNum BQM variables: ", len(list(self.bqm.variables)))
        if not self.energy is None:
            print("Energy: ", self.energy)
        print("Model time: ", model_time)
        print("Solving time: ", self.solving_time, "\n\n")


    def print_list(self,  model_time = 0):
        if self.flights is None or self.aircraft is None:
            print("Not possible to print solution")
            return None

        number_flights_per_aircraft_model = {}
        flight_minutes_per_aircraft_model = {}     
        for aircraft in self.aircraft:
            if not aircraft.model.model in number_flights_per_aircraft_model:
                number_flights_per_aircraft_model.update({aircraft.model.model: 0})
                flight_minutes_per_aircraft_model.update({aircraft.model.model: 0})
        for aircraft_index, solution_aircraft in enumerate(self.matrix):
            number_flights = 0
            number_flight_minutes = 0
            aircraft = self.aircraft[aircraft_index]
            aircraft_print = aircraft.plate + ": "
            for activity in solution_aircraft:
                if isinstance(activity, Flight):
                    number_flights += 1
                    number_flight_minutes += activity.activity_time
                aircraft_print += activity.short_repr() +", "
            number_flights_per_aircraft_model[aircraft.model.model] += number_flights
            flight_minutes_per_aircraft_model[aircraft.model.model] += number_flight_minutes
            print(aircraft_print)
        

        self.number_flights_per_aircraft_model = number_flights_per_aircraft_model
        #self.stdev_number_flights_per_aircraft_model = statistics.stdev(number_flights_per_aircraft)
        self.flight_minutes_per_aircraft_model = flight_minutes_per_aircraft_model
        #self.stdev_flight_minutes_per_aircraft = statistics.stdev(flight_minutes_per_aircraft)
        print("Number flights per aircraft: ", self.number_flights_per_aircraft_model)
        print("Number flight hours per aircraft: ", self.flight_minutes_per_aircraft_model)        
        print("Total cost: ", self.total_cost)
        print("Free seats: ", self.nmb_free_seats)
        print("Extra flights required: ", self.nmb_extra_flights_required)
        print("Not assigned flights: ", self.nmb_not_assigned_flights)
        
        
        print("\n\nNum BQM variables: ", len(list(self.bqm.variables)))
        if not self.energy is None:
            print("Energy: ", self.energy)
        print("Model time: ", model_time)
        print("Solving time: ", self.solving_time, "\n\n")

    
    def print_export(self, total_flights, print_matrix=False, model_time = 0):
        result = ""
        if self.activities == []:
            self.get_activities()
        for solution_aircraft in self.matrix:
            for flight in total_flights:
                if flight in solution_aircraft:
                    result += str(1)
                else:
                    result += str(0)
        self.print_list(model_time=model_time)
        data = {}
        data['hamming'] = result
        data['energy'] = self.energy
        data['model_time_seconds'] = model_time
        data['solving_time_seconds'] = self.solving_time
        data['num_variables'] = len(list(self.bqm.variables))
        data['fixed_variables'] = len(self.fixed_var)
        data['aux_variables'] = len(list(filter(lambda bqm_var: len(str(bqm_var)) > 3, list(self.bqm.variables))))
        data['num_flights_per_aircraft_model'] = self.number_flights_per_aircraft_model
        data['flight_minutes_per_aircraft_model'] = self.flight_minutes_per_aircraft_model
        data['total_cost'] = self.total_cost
        data['free_seats'] = self.nmb_free_seats
        data['extra_flights'] = self.nmb_extra_flights_required
        data['not_assigned_flights'] = self.nmb_not_assigned_flights
        i=0
        basic_folder = ""
        path_file = ""
        while i < 4:
            if i == 0:
                path_file = ('data/generated/{num_aircraft}_aircraft/{num_flights}_flights/flights{num_flights}.csv').format(num_flights = len(total_flights), num_aircraft= len(self.matrix))
            else:
                path_file = ('data/generated/{num_aircraft}_aircraft/{num_flights}_flights/flights{num_flights}_{iteration}.csv').format(num_flights = len(total_flights), num_aircraft= len(self.matrix), modulation = self.modulation, iteration=i)
            if not pathlib.Path(path_file).exists():
                break
            i += 1

        parts = [path_file[:path_file.rfind('/')], path_file[path_file.rfind('/'):len(path_file)-4]]
        basic_folder = parts[0]+'/'+self.modulation+parts[1]+'/'+self.sampler.name
        pathlib.Path(basic_folder).mkdir(parents=True, exist_ok=True)    
        
        filename = '{basic_folder}/flights-{num_flights}-aircraft-{num_aircraft}-{date:%Y-%m-%d_%H:%M:%S}.json'.format( date=datetime.datetime.now(), num_flights = len(total_flights), num_aircraft= len(self.matrix), basic_folder = basic_folder)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()

        if len(result) != len(total_flights)*len(self.aircraft):
            print("Error")
    

    def verify_relaxed(self):
        all_flights = []
        free_seats = 0
        total_cost = 0
        extra_flights = 0
        
        global_activities = deepcopy(self.flights)

        for aircraft in self.aircraft:
            global_activities += aircraft.maintenances 
        global_activities.sort()
        global_activities = set(global_activities)
        
        for aircraft_index, aircraft_ref in enumerate(self.aircraft):
            activities = self.matrix[aircraft_index]
            total_cost += aircraft_ref.get_operational_cost(activities)
            global_activities -= set(activities)
            for index, activity in enumerate(activities):
                if index < len(activities) - 1:
                    next_activity = activities[index+1]
                    if activity.check_overlap(next_activity):
                        #print("\n\nInvalid assignment because overlap: \n\nActivity 1:\n", activity, "\n\nActivity 2:\n", next_activity, "\n\nAircraft:\n", aircraft_ref.plate,"\n\n")
                        return False
                    if activity.destination != next_activity.origin:
                        if not isinstance(activity, Maintenance) and not isinstance(next_activity, Maintenance):
                            #print("\n\nAircraft:\n", aircraft_ref.plate, "\n\nWill require an extra flight to perform both: \n\n Activity 1:\n", activity, "\n\n Activity 2: \n", next_activity, "\n\n")
                            return False
                        else:
                            #print("\n\nAircraft:\n", aircraft_ref.plate, "\n\nWill require an extra flight to perform both: \n\n Activity 1:\n", activity, "\n\n Activity 2: \n", next_activity, "\n\n")
                            extra_flights += 1
                if hasattr(activity, 'aircraft_model'):
                    if activity.aircraft_model != aircraft_ref.model:
                        #print("\n\nInvalid assignment because of aircraft model: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                        return False
                else:
                    if isinstance(activity, Flight) and activity.aircraft_fleet.value > aircraft_ref.model.fleet.value:
                        #print("\n\nInvalid assignment because of aircraft fleet: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                        return False
                if isinstance(activity, Flight):
                        if activity.needed_seats > aircraft_ref.total_seats:
                            #print("\n\nInvalid assignment because of seats: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                            return False
                        else:
                            free_seats += aircraft_ref.total_seats-activity.needed_seats
                            all_flights.append(activity)


        if len(all_flights) != len(set(all_flights)):
            for index, flight in enumerate(all_flights[len(all_flights)-1:]):
                for other_flight in all_flights[index+1:]:
                    if flight == other_flight:
                        #print("\n\nInvalid assignment: \nFlight: ", self.flights[flight], "\n\nIs being assignment to more than one aicraft\n\n")
                        return False
        
        self.total_cost = total_cost
        self.nmb_extra_flights_required = extra_flights
        self.nmb_not_assigned_flights = len(global_activities)
        self.nmb_free_seats = free_seats
        print("FREE SEATS: ", self.nmb_free_seats)
        print("TOTAL_COST ", self.total_cost)
        print("EXTRA FLIGHTS: ", self.nmb_extra_flights_required)
        print("NOT ASSIGNED FLIGHTS: ", self.nmb_not_assigned_flights)
        return True
    
    def verify(self):
        all_flights = []
        free_seats = 0
        total_cost = 0
        extra_flights = 0
        
        global_activities = deepcopy(self.flights)

        for aircraft in self.aircraft:
            global_activities += aircraft.maintenances 
        global_activities.sort()
        global_activities = set(global_activities)
        
        for aircraft_index, aircraft_ref in enumerate(self.aircraft):
            activities = self.matrix[aircraft_index]
            total_cost += aircraft_ref.get_operational_cost(activities)
            global_activities -= set(activities)
            for index, activity in enumerate(activities):
                if index < len(activities) - 1:
                    next_activity = activities[index+1]
                    if activity.check_overlap(next_activity):
                        #print("\n\nInvalid assignment because overlap: \n\nActivity 1:\n", activity, "\n\nActivity 2:\n", next_activity, "\n\nAircraft:\n", aircraft_ref.plate,"\n\n")
                        return False
                    if activity.destination != next_activity.origin:
                        return False
                if hasattr(activity, 'aircraft_model'):
                    if activity.aircraft_model != aircraft_ref.model:
                        #print("\n\nInvalid assignment because of aircraft model: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                        return False
                else:
                    if isinstance(activity, Flight) and activity.aircraft_fleet.value > aircraft_ref.model.fleet.value:
                        #print("\n\nInvalid assignment because of aircraft fleet: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                        return False
                if isinstance(activity, Flight):
                        if activity.needed_seats > aircraft_ref.total_seats:
                            #print("\n\nInvalid assignment because of seats: \n\nActivity: ", activity, "\n\nAircraft: ", aircraft_ref,"\n\n")
                            return False
                        else:
                            free_seats += aircraft_ref.total_seats-activity.needed_seats
                            all_flights.append(activity)


        if len(all_flights) != len(set(all_flights)):
            for index, flight in enumerate(all_flights[len(all_flights)-1:]):
                for other_flight in all_flights[index+1:]:
                    if flight == other_flight:
                        #print("\n\nInvalid assignment: \nFlight: ", self.flights[flight], "\n\nIs being assignment to more than one aicraft\n\n")
                        return False
        
        self.total_cost = total_cost
        self.nmb_extra_flights_required = extra_flights
        self.nmb_not_assigned_flights = len(global_activities)
        self.nmb_free_seats = free_seats
        print("FREE SEATS: ", self.nmb_free_seats)
        print("TOTAL_COST ", self.total_cost)
        print("EXTRA FLIGHTS: ", self.nmb_extra_flights_required)
        print("NOT ASSIGNED FLIGHTS: ", self.nmb_not_assigned_flights)
        return True
    
    def message_verify(self):
        all_flights = []
        free_seats = 0
        total_cost = 0
        flights_cost = 0

        global_activities = deepcopy(self.flights)

        for aircraft in self.aircraft:
            global_activities += aircraft.maintenances 
        global_activities.sort()
        global_activities = set(global_activities)
        
        for aircraft_index, aircraft_ref in enumerate(self.aircraft):
            activities = self.matrix[aircraft_index]
            total_cost += aircraft_ref.get_operational_cost(activities)
            flights_cost += aircraft_ref.get_flights_cost(activities)
            global_activities -= set(activities)
            for index, activity in enumerate(activities):
                if index < len(activities) - 1:
                    next_activity = activities[index+1]
                    if activity.check_overlap(next_activity):
                        m = "Invalid assignment because overlap: Activity 1:"+ str(activity.original_activity_index)+ " Activity 2: "+ str(next_activity.original_activity_index)+ "Aircraft: "+ str(aircraft_ref.index)
                        return False, m, None, None, None
                    if activity.destination != next_activity.origin:
                        m = "Invalid assignment because no path: Activity 1:"+ str(activity.original_activity_index)+ " Activity 2: "+ str(next_activity.original_activity_index)+ "Aircraft: "+ str(aircraft_ref.index)
                        return False, m, None, None, None
                if hasattr(activity, 'aircraft_model'):
                    if activity.aircraft_model != aircraft_ref.model:
                        m = "Invalid assignment because of aircraft model: Activity: "+ str(activity.original_activity_index)+ " Aircraft: "+ str(aircraft_ref.index)
                        return False, m, None, None, None
                else:
                    if isinstance(activity, Flight) and activity.aircraft_fleet.value > aircraft_ref.model.fleet.value:
                        m = "Invalid assignment because of aircraft fleet: Flight: "+ str(activity.original_flight_index)+ " Aircraft: "+ str(aircraft_ref.index)
                        return False, m, None, None, None
                if isinstance(activity, Flight):
                        if activity.needed_seats > aircraft_ref.total_seats:
                            m = "Invalid assignment because of seats: Flight: "+ str(activity.original_flight_index)+ " Aircraft: "+ str(aircraft_ref.index)
                            return False, m, None, None, None
                        else:
                            free_seats += aircraft_ref.total_seats-activity.needed_seats
                            all_flights.append(activity)


        if len(global_activities) > 0:
            m = "Activities: "
            for global_act in global_activities:
                m += str(global_act.original_activity_index) + ","
            m += " are not assigned"
            return False, m, free_seats, total_cost, flights_cost
        if len(all_flights) != len(set(all_flights)):
            for index, flight in enumerate(all_flights[len(all_flights)-1:]):
                for other_flight in all_flights[index+1:]:
                    if flight == other_flight:
                        m = "Flight: " + str(flight.original_flight_index) + " Is being assignment to more than one aicraft"
                        return False, m, free_seats, total_cost, flights_cost
        return True, None, free_seats, total_cost, flights_cost
    
    def get_activities(self):
        activities = []
        activities += self.flights
        for aircraft in self.aircraft:
            activities += aircraft.maintenances
        activities.sort()
        self.activities = activities
    
    def is_incomplete(self, other_solution):
        if self.activities == []:
            self.get_activities()
        if other_solution.activities == []:
            other_solution.get_activities()
        if len(set(other_solution.activities).difference(self.activities)) > 0:
            return True
        else:
            return False
