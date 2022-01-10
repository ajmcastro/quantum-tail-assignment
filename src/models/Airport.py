from models.AircraftModelFleet import AircraftFleet

class Airport:
    
    def __init__(self, code, nb_landing_cost, nb_parking_cost, wb_landing_cost, wb_parking_cost):
        super().__init__()
        self.iata_code = code
        self.nb_landing_cost = float(nb_landing_cost) # landing cost per landing for narrow-body aircraft
        self.nb_parking_cost = float(nb_parking_cost) # parking cost per day for narrow-body aircraft
        self.wb_landing_cost = float(wb_landing_cost) # landing cost per landing for wide-body aircraft
        self.wb_parking_cost = float(wb_parking_cost) # parking cost per day for wide-body aircraft

    def __eq__(self, other):
        if not hasattr(other, 'iata_code'): # to allow both loading (self.iata_code == other) and comparison on constraints (self.iata_code == other.iata_code) 
            return self.iata_code == other
        return self.iata_code == other.iata_code
    
    def __hash__(self):
        return hash(self.iata_code)
        
    def __repr__(self):
        return ("{{IATA: {iata_code}, NB Landing: {nb_landing_cost}, NB parking: {nb_parking_cost}, WB Landing: {wb_landing_cost}, WB Parking: {wb_parking_cost}}}").format(**vars(self))

    def get_parking_cost(self, time_min, aircraft_fleet):
         if aircraft_fleet == AircraftFleet.NB:
             return time_min*self.nb_parking_cost/1440
         else:
             return time_min*self.wb_parking_cost/1440
