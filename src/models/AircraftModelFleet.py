from enum import Enum
from datetime import timedelta
import scheduler.GenericMacros as macros

class AircraftFleet(Enum):
    NB = 0
    WB = 1

class AircraftModel:
    def __init__(self, model, fleet, atc_avg_cost_naut_mile, maint_avg_cost_min, fuel_avg_cost_min, airp_handling_cost):
        super().__init__()
        self.model = model
        if fleet == 'NB':
            self.fleet = AircraftFleet.NB
        else:
            self.fleet = AircraftFleet.WB
        self.atc_avg_cost_naut_mile = float(atc_avg_cost_naut_mile) #air traffic control average cost per nautic mile
        self.maint_avg_cost_min = float(maint_avg_cost_min) #maintenance average cost per minute
        self.fuel_avg_cost_min = float(fuel_avg_cost_min) #fuel average cost per minute (flying)
        self.airp_handling_cost = float(airp_handling_cost) #airport handling cost
    
    def __eq__(self, other):
        return self.model == other

    def __repr__(self):
        return ("{{Model: {model}, Fleet: {fleet}, ATC_AVG_COST: {atc_avg_cost_naut_mile}, FUEL_AVG_COST: {fuel_avg_cost_min}, HANDLING_COST: {airp_handling_cost}}}").format(**vars(self))
    
    def get_operational_cost(self, schedule):
        cost = 0
        for index, activity in enumerate(schedule):
            cost += activity.get_model_execution_cost(self)
            if index < len(schedule) - 1:
                next_activity = schedule[index+1]
                if activity.destination == next_activity.origin:
                    #parking_cost
                    if self.fleet == AircraftFleet.NB:
                        daily_parking_cost = activity.destination.nb_parking_cost
                    else:
                        daily_parking_cost = activity.destination.wb_parking_cost
                    cost += (float((next_activity.start_time - activity.end_time - timedelta(minutes=macros.MIN_ROTATION_TIME)).total_seconds()/60)*daily_parking_cost)/1440
        return cost
    
