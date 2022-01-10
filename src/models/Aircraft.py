from models.Activity import Flight
from models.AircraftModelFleet import AircraftFleet, AircraftModel
import scheduler.GenericMacros as macros
from datetime import timedelta

class Aircraft:
    def __init__(self, index, plate, name, model, business_seats, economic_seats):
        super().__init__()
        self.index = int(index)
        self.plate = plate
        self.name = name
        self.model = model #aircraft model object
        self.business_seats = int(business_seats)
        self.economic_seats = int(economic_seats)
        self.total_seats = self.business_seats + self.economic_seats
        self.overlap_flights = set()
        self.overlap_flights_indexes = set()
        self.previous_activity = None
        self.possible_flight_after_previous_activity = set()
        self.following_activity = None
        self.possible_flight_before_following_activity = set()
        self.impossible_flights = set()
        self.not_recommended_flights = set()
        self.maintenances = []

    def add_overlap_flight(self, overlap_flight):
        self.overlap_flights.update({overlap_flight})
        self.overlap_flights_indexes.update({overlap_flight.flight_index})
        self.possible_flight_before_following_activity -= set({overlap_flight})
        self.possible_flight_after_previous_activity -= set({overlap_flight})

    def reset_overlaps(self):
        self.overlap_flights = set()
        self.overlap_flights_indexes = set()
    
    def add_maintenance(self, maintenance):
        self.maintenances.append(maintenance)
    
    def set_maintenances(self, maintenances):
        self.maintenances = maintenances

    def group_maintenances(self):
        maintenance1_index = 0
        while maintenance1_index < len(self.maintenances)-1:
            maintenance1 = self.maintenances[maintenance1_index]
            maintenance2_index = maintenance1_index+1
            while maintenance2_index < len(self.maintenances):
                maintenance2 = self.maintenances[maintenance2_index]
                if maintenance1.check_overlap(maintenance2):
                    if maintenance1.destination == maintenance2.origin:   
                        self.maintenances[maintenance1_index].end_time = maintenance2.end_time
                        self.maintenances[maintenance1_index].check_type_code += "+"+maintenance2.check_type_code  
                        maintenance2_index -= 1
                    self.maintenances.remove(maintenance2)
                maintenance2_index += 1
            maintenance1_index += 1
    
    def add_maintenance_connection_flight(self, flight):

        # add flight as posterior flight for the proper maintenance
        for maintenance_index in range(len(self.maintenances)-1, -1, -1):
            if self.maintenances[maintenance_index] < flight and self.maintenances[maintenance_index].destination == flight.origin:
                self.maintenances[maintenance_index].add_pos_flight(flight)
                break

        # add flight as previous flight fot the proper maintenance
        for maintenance_index in range(len(self.maintenances)):
            if self.maintenances[maintenance_index] > flight and self.maintenances[maintenance_index].origin == flight.destination:
                self.maintenances[maintenance_index].add_prev_flight(flight)
                break


    def set_previous_activity(self, previous_activity):
        self.previous_activity = previous_activity
    
    def set_following_activity(self, following_activity):
        self.following_activity = following_activity

    def add_possible_flight_after_previous_activity(self, flight):
        self.possible_flight_after_previous_activity.update({flight})
    
    def add_possible_flight_before_following_activity(self, flight):
        self.possible_flight_before_following_activity.update({flight})
    
    def reset_possible_flights_after_previous_activity(self):
        self.possible_flight_after_previous_activity = set()

    def reset_possible_flights_before_following_activity(self):
        self.possible_flight_before_following_activity = set()
    
    def add_impossible_flight(self, flight):
        self.impossible_flights.update({flight})
        self.possible_flight_before_following_activity -= set({flight})
        self.possible_flight_after_previous_activity -= set({flight})
    
    def add_not_recommended_flight(self, flight):
        self.not_recommended_flights.update({flight})
    
    def reset_impossible_flights(self):
        self.impossible_flights = set()
    
    def reset_not_recommended_flights(self):
        self.not_recommended_flights = set()
    
    # def reset_window(self):
    #     self.reset_impossible_flights()
    #     self.reset_not_recommended_flights()
    #     self.reset_possible_flights_after_previous_activity()
    #     self.reset_possible_flights_before_following_activity()
    #     for maintenance in self.maintenances:
    #         maintenance.reset_prev_pos_flights()
        
    def __eq__(self, other):
        if hasattr(other, 'plate'):
            return self.plate == other.plate
        else:
            return self.plate == other

    def __repr__(self):
        rep = "{{Index: {index}, Plate: {plate}, Name: {name}, Model: {model.model}, Total_Seats: {total_seats}, Business_Seats: {business_seats}, Economic_Seats: {economic_seats}\n"
        if len(self.overlap_flights) > 0:
            rep += "Overlap flights:\n"
            for activity in self.overlap_flights:
                rep += activity._repr_str_() + "\n"
        rep += "}}"  
        return (rep).format(**vars(self))

    def is_flight_compatible(self, flight):
        if hasattr(flight, 'aircraft_model'):
            if flight.aircraft_model == self.model:
                return self.has_enough_space(flight)
            else:
                return False
        else:
            if flight.aircraft_fleet.value <= self.model.fleet.value:
                return self.has_enough_space(flight)
            else:
                return False
    
    def is_flight_impossible_on_restrictions(self, flight):
        if len(self.impossible_flights) > 0 and flight in self.impossible_flights:
            return True
        else:
            return False
    
    def has_enough_space(self, activity):
        return activity.needed_seats <= self.total_seats
    
    def is_flight_overlapping_maintenance(self, flight):
        if len(self.maintenances) == 0:
            return False
        for maintenance in self.maintenances:
            if maintenance.check_overlap(flight):
                return True
        return False

    def can_perform_flight(self, flight):
        if self.is_flight_impossible_on_restrictions(flight):
            return False
        if self.is_flight_compatible(flight):
            return not (flight in self.overlap_flights)
        else:
            return False
    
    def get_operational_cost(self, schedule):
        cost = 0
        for index, activity in enumerate(schedule):
            cost += activity.get_execution_cost(self)
            if index < len(schedule) - 1:
                next_activity = schedule[index+1]
                if activity.destination == next_activity.origin:
                    #parking_cost
                    if self.model.fleet == AircraftFleet.NB:
                        daily_parking_cost = activity.destination.nb_parking_cost
                    else:
                        daily_parking_cost = activity.destination.wb_parking_cost
                    cost += (float((next_activity.start_time - activity.end_time - timedelta(minutes=macros.MIN_ROTATION_TIME)).total_seconds()/60)*daily_parking_cost)/1440
        return cost
    
    def get_flights_cost(self, schedule):
        cost = 0
        for activity in schedule:
            if isinstance(activity, Flight):
                cost += activity.get_execution_cost(self)
        return cost





        

