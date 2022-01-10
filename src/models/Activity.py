import scheduler.GenericMacros as macros
from models.AircraftModelFleet import AircraftFleet
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class Activity(ABC):
    
    def __init__(self, index, origin, destination, start_time, end_time):
        super().__init__()
        self.activity_index = int(index)
        self.original_activity_index = int(index)
        self.origin = origin
        self.destination = destination
        if isinstance(start_time, datetime):
            self.start_time = start_time
        else:
            self.start_time = datetime.strptime(start_time, "%d/%m/%Y %H:%M")
        if isinstance(end_time, datetime):
            self.end_time = end_time
        else:
            self.end_time = datetime.strptime(end_time, "%d/%m/%Y %H:%M")
        self.activity_time = float((self.end_time - self.start_time).total_seconds()/60)
    
    def __lt__(self, other):
        if self.start_time == other.start_time:
            return self.end_time < other.end_time
        else:
            return self.start_time < other.start_time

    def __gt__(self, other):
        if self.start_time == other.start_time:
            return self.end_time >= other.end_time
        return self.start_time >= other.start_time
    
    def reset_activity_index(self, index):
        self.activity_index = index
    
    def set_original_index(self, index):
        self.original_activity_index = index
    
    # first case checks by index
    #second case works as fallback and checks by other atributes
    def __eq__(self, value):
        return self.original_activity_index == value.original_activity_index or (self.__class__.__name__ == value.__class__.__name__ and self.origin == self.origin and self.destination == value.destination and self.start_time == value.start_time and self.end_time == value.end_time)
    
    def __hash__(self):
        return self.original_activity_index

    # 5 -> Check overlap activities following regulamentary laws (e.g. rotation time between flights)
    def check_overlap(self, other_activity):
        weighted_self_initial_time = self.start_time - timedelta(minutes=macros.MIN_ROTATION_TIME)
        weighted_self_final_time = self.end_time + timedelta(minutes=macros.MIN_ROTATION_TIME)
        if other_activity.end_time <= weighted_self_initial_time or other_activity.start_time >= weighted_self_final_time:
            return False
        else:
            return True

    def has_direct_connection(self, destination):
        return self.destination == destination.origin
    
    def compatible_flight(self, flight):
        raise NotImplementedError('compatible_flight function is not implemented')

class Flight(Activity):
    def __init__(self, index, flight_index, number, origin, destination, aircraft_model_fleet, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, flight_distance, has_aircraft_model):
        super().__init__(index, origin, destination, start_time, end_time)
        self.flight_index = int(flight_index)
        self.original_flight_index = int(flight_index)
        self.number = number
        self.has_aircraft_model = bool(has_aircraft_model)
        self.business_seats = int(business_seats)
        self.economic_seats = int(economic_seats)
        self.business_seats_sold = int(business_seats_sold)
        self.economic_seats_sold = int(economic_seats_sold)
        self.flight_distance = float(flight_distance)
        if has_aircraft_model:
            self.aircraft_model = aircraft_model_fleet
        else:
            if isinstance(aircraft_model_fleet, AircraftFleet):
                self.aircraft_fleet = aircraft_model_fleet
            else:
                if aircraft_model_fleet == 'NB':
                    self.aircraft_fleet = AircraftFleet.NB
                else:
                    self.aircraft_fleet = AircraftFleet.WB
        self.needed_seats = int(business_seats)+int(economic_seats)
    
    def __eq__(self, other):
        if hasattr(other, 'original_flight_index'):
            return self.original_flight_index == other.original_flight_index
        elif hasattr(other, 'activity_index'):
            return self.original_activity_index == other.original_activity_index or (self.__class__.__name__ == other.__class__.__name__ and self.origin == self.origin and self.destination == other.destination and self.start_time == other.start_time and self.end_time == other.end_time)
        else:
            return self.original_flight_index == other

    
    def get_cost(self, aircraft):
        if hasattr(self, 'aircraft_model'):
            aircraft_model = self.aircraft_model
        else:
            aircraft_model = aircraft.model
        
        if aircraft_model.fleet == AircraftFleet.NB:
            origin_landing_cost = self.origin.nb_landing_cost
            destination_landing_cost = self.destination.nb_landing_cost
            origin_daily_parking_cost = self.origin.nb_parking_cost
            destination_daily_parking_cost = self.destination.nb_parking_cost
        else:
            origin_landing_cost = self.origin.wb_landing_cost
            destination_landing_cost = self.destination.wb_landing_cost
            origin_daily_parking_cost = self.origin.wb_parking_cost
            destination_daily_parking_cost = self.destination.wb_parking_cost

        execution_cost = origin_landing_cost + destination_landing_cost + aircraft_model.airp_handling_cost + (self.activity_time*aircraft_model.fuel_avg_cost_min)+(self.flight_distance*aircraft_model.atc_avg_cost_naut_mile)+ (macros.MIN_ROTATION_TIME/2*origin_daily_parking_cost)/1440 + (macros.MIN_ROTATION_TIME/2*destination_daily_parking_cost)/1440

        return execution_cost
    
    def get_execution_cost(self, aircraft):
        if hasattr(self, 'aircraft_model'):
            aircraft_model = self.aircraft_model
        else:
            aircraft_model = aircraft.model

        if aircraft_model.fleet == AircraftFleet.NB:
            origin_landing_cost = self.origin.nb_landing_cost
            destination_landing_cost = self.destination.nb_landing_cost
            origin_daily_parking_cost = self.origin.nb_parking_cost
            destination_daily_parking_cost = self.destination.nb_parking_cost
        else:
            origin_landing_cost = self.origin.wb_landing_cost
            destination_landing_cost = self.destination.wb_landing_cost
            origin_daily_parking_cost = self.origin.wb_parking_cost
            destination_daily_parking_cost = self.destination.wb_parking_cost

        execution_cost = origin_landing_cost + destination_landing_cost + aircraft_model.airp_handling_cost + (self.activity_time*aircraft_model.fuel_avg_cost_min)+(self.flight_distance*aircraft_model.atc_avg_cost_naut_mile)+ (macros.MIN_ROTATION_TIME/2*origin_daily_parking_cost)/1440 + (macros.MIN_ROTATION_TIME/2*destination_daily_parking_cost)/1440

        return execution_cost

    def get_model_execution_cost(self, model):

        if model.fleet == AircraftFleet.NB:
            origin_landing_cost = self.origin.nb_landing_cost
            destination_landing_cost = self.destination.nb_landing_cost
            origin_daily_parking_cost = self.origin.nb_parking_cost
            destination_daily_parking_cost = self.destination.nb_parking_cost
        else:
            origin_landing_cost = self.origin.wb_landing_cost
            destination_landing_cost = self.destination.wb_landing_cost
            origin_daily_parking_cost = self.origin.wb_parking_cost
            destination_daily_parking_cost = self.destination.wb_parking_cost

        execution_cost = origin_landing_cost + destination_landing_cost + model.airp_handling_cost + (self.activity_time*model.fuel_avg_cost_min)+(self.flight_distance*model.atc_avg_cost_naut_mile)+ (macros.MIN_ROTATION_TIME/2*origin_daily_parking_cost)/1440 + (macros.MIN_ROTATION_TIME/2*destination_daily_parking_cost)/1440

        return execution_cost

    def __repr__(self):
        if self.has_aircraft_model:
            return ("{{Activity Index: {activity_index}, Original Flight Index: {original_flight_index},  Number: {number}, Origin: {origin.iata_code}, Destination: {destination.iata_code}, Aircraft Model: {aircraft_model}, Needed Seats: {needed_seats}, Departure Time: {start_time}, Arrival Time: {end_time}}}").format(**vars(self))
        else:
            return ("{{Activity Index: {activity_index}, Original Flight Index: {original_flight_index},  Number: {number}, Origin: {origin.iata_code}, Destination: {destination.iata_code}, Aircraft Fleet: {aircraft_fleet}, Needed Seats: {needed_seats}, Departure Time: {start_time}, Arrival Time: {end_time}}}").format(**vars(self))

    def _repr_str_(self):
        if self.has_aircraft_model:
            return ("Activity Index: {activity_index}, Original Flight Index: {original_flight_index}, Number: {number}, Origin: {origin.iata_code}, Destination: {destination.iata_code}, Aircraft Model: {aircraft_model}, Needed Seats: {needed_seats}, Departure Time: {start_time}, Arrival Time: {end_time}").format(**vars(self))
        else:
            return ("Activity Index: {activity_index}, Original Flight Index: {original_flight_index}, Number: {number}, Origin: {origin.iata_code}, Destination: {destination.iata_code}, Aircraft Fleet: {aircraft_fleet}, Needed Seats: {needed_seats}, Departure Time: {start_time}, Arrival Time: {end_time}").format(**vars(self))
    
    def short_repr(self):
        return ("Flight: {original_flight_index}|{origin.iata_code}|{start_time.day}/{start_time.month}/{start_time.year}T{start_time.hour}:{start_time.minute}->{destination.iata_code}|{end_time.day}/{end_time.month}/{end_time.year}T{end_time.hour}:{end_time.minute}").format(**vars(self))

    def compatible_flight(self, flight):
        """
        Check if this flight is compatible with the given flight. For being compatible both flights must be from the same aircraft_model or if aircraft_model is not defined then both flights are compatible since although having a minimum required fleet, all flights can be operated by an aircraft from an higher fleet

        Arguments:
            flight {Flight} -- flight to be analysed

        Returns:
            boolean -- True if the flight is compatible with this flight and False otherwise
        """
        
        if not isinstance(flight, Flight):
            return False
        if hasattr(self, 'aircraft_model'):
            return self.aircraft_model == flight.aircraft_model # both activities have a pre defined aircraft model and therefore only if it is the same the activities are compatible  
        else:
            return True


    def set_local_index(self, index):
        self.flight_index = index
    
    def __hash__(self):
        return self.original_activity_index

class ComposedFlight(Flight):
    def __init__(self, index, flight_index, number, origin, destination, aircraft_model_fleet, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, distance, has_aircraft_model, costs, composed_by_flights):
        super().__init__(index, flight_index, number, origin, destination, aircraft_model_fleet, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, distance, has_aircraft_model)
        self.costs = costs
        self.composed_by_flights = composed_by_flights
    
    def get_cost(self, aircraft):
        return self.costs[aircraft.model.model]

    def get_execution_cost(self, aircraft):
        return self.costs[aircraft.model.model]
    
    def csv_repr(self):
        costs = [self.costs[cost] for cost in self.costs]
        elem = [self.number, self.origin.iata_code, self.destination.iata_code, AircraftFleet(self.aircraft_fleet).name, self.start_time.strftime("%d/%m/%Y %H:%M"), self.end_time.strftime("%d/%m/%Y %H:%M"), self.business_seats, self.economic_seats, self.business_seats_sold, self.economic_seats_sold, self.flight_distance] + costs + [self.composed_by_flights]
        return elem


class Maintenance(Activity):
    def __init__(self, index, maintenance_index, check_type_code, start_time, end_time, airport, status, has_aircraft_model):
        super().__init__(index, airport, airport, start_time, end_time)
        self.maintenance_index = int(maintenance_index)
        self.original_maintenance_index = int(maintenance_index)
        self.check_type_code = check_type_code
        self.status = status
        self.prev_flights = []
        self.pos_flights = []
    
    def __eq__(self, other):
        if hasattr(other, 'original_maintenance_index'):
            return self.original_maintenance_index == other.original_maintenance_index
        elif hasattr(other, 'activity_index'):
            return self.original_activity_index == other.original_activity_index or (self.__class__.__name__ == other.__class__.__name__ and self.origin == self.origin and self.destination == other.destination and self.start_time == other.start_time and self.end_time == other.end_time)
        else:
            return self.original_maintenance_index == other

    
    def __repr__(self):
        return ("{{Activity Index: {activity_index}, Maintenance Index: {maintenance_index}, CheckTypeCode: {check_type_code}, Start Time: {start_time}, End Time: {end_time}, Airport: {origin.iata_code}}}").format(**vars(self))

    def _repr_str_(self):
        return ("Activity Index: {activity_index}, Maintenance Index: {maintenance_index}, CheckTypeCode: {check_type_code}, Start Time: {start_time}, End Time: {end_time}, Airport: {origin.iata_code}").format(**vars(self))
    
    def short_repr(self):
        return ("Maintenance: {original_maintenance_index}|{origin.iata_code}|{start_time.day}/{start_time.month}/{start_time.year}T{start_time.hour}:{start_time.minute}->{end_time.day}/{end_time.month}/{end_time.year}T{end_time.hour}:{end_time.minute}").format(**vars(self))
    
    def add_pos_flight(self, flight):
        self.pos_flights.append(flight)
    
    def add_prev_flight(self, flight):
        self.prev_flights.append(flight)
    
    def remove_pos_flight(self, flight):
        self.pos_flights.remove(flight)
    
    def set_local_index(self, index):
        self.maintenance_index = index
        self.prev_flights = []
        self.pos_flights = []
    
    def set_just_local_index(self, index):
        self.maintenance_index = index
    
    def reset_prev_pos_flights(self):
        self.prev_flights = []
        self.pos_flights = []
    
    def __hash__(self):
        return self.original_activity_index
    
    def get_execution_cost(self, aircraft):
        if aircraft.model.fleet == AircraftFleet.NB:
            daily_parking_cost = self.origin.nb_parking_cost
        else:
            daily_parking_cost = self.origin.wb_parking_cost
        return self.activity_time*aircraft.model.maint_avg_cost_min + (macros.MIN_ROTATION_TIME*daily_parking_cost)/1440