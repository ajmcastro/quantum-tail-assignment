import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
import csv
from datetime import datetime
from models.Aircraft import AircraftModel

files_dir = "data/final/model5/"


# ----------------- CITY PAIRS -------------------- #

class StructuredCityPair:
    def __init__(self, origin, destination, distance_naut_mile, distance_km):
        super().__init__()
        self.origin = origin
        self.destination = destination
        self.distance_naut_mile = distance_naut_mile
        self.distance_km = distance_km
    
def filterCityPairs():
    airports = []
    city_pairs = []
    with open(files_dir+"airports.csv") as airports_row:
        reader = csv.DictReader(airports_row)
        for row in reader:
            airports.append(row["Iata_Code"])
    airports_row.close()
    with open(files_dir+"unstructured_city_pairs.csv") as city_pair_row:
        reader = csv.DictReader(city_pair_row)
        for row in reader:
            if row["Origin"] in airports and row["Destination"] in airports:
                city_pairs.append(StructuredCityPair(row["Origin"], row["Destination"], row["Distance_In_Nautical_Miles"], row["Distance_In_Km"]))
    city_pair_row.close()
    row_list = []
    row_list.append(["Origin","Destination","Distance_In_Nautical_Miles","Distance_In_Km"])
    for city_pair in city_pairs:
        row = []
        row.append(city_pair.origin)
        row.append(city_pair.destination)
        row.append(city_pair.distance_naut_mile)
        row.append(city_pair.distance_km)
        row_list.append(row)

    with open(files_dir+'structured_city_pairs.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()



# --------------- AIRPORTS --------------------- #

class StrcuturedAirport:
    def __init__(self, iata_code, nb_landing_cost, nb_daily_parking_cost, wb_landing_cost, wb_daily_parking_cost):
        super().__init__()
        self.iata_code = iata_code
        self.nb_landing_cost = nb_landing_cost
        self.nb_daily_parking_cost = nb_daily_parking_cost
        self.wb_landing_cost = wb_landing_cost
        self.wb_daily_parking_cost = wb_daily_parking_cost


def getStructuredAirports(flights_filename, maintenances_filename):
    airports_code = set()
    airports = []
    with open(files_dir+flights_filename) as flights_row:
        reader = csv.DictReader(flights_row)
        for row in reader:
           airports_code.update({row["Origin"]})
           airports_code.update({row["Destination"]})
    flights_row.close()
    with open(files_dir+maintenances_filename) as maintenances_row:
        reader = csv.DictReader(maintenances_row)
        for row in reader:
           airports_code.update({row["Airport"]})
    maintenances_row.close()
    with open(files_dir+"unstructured_airports.csv") as airports_row:
        reader = csv.DictReader(airports_row)
        for row in reader:
            if row["Iata_Code"] in airports_code:
                airports.append(StrcuturedAirport(row["Iata_Code"], row["Nb_Landing_Cost_Per_Landing"], row["Nb_Daily_Parking_Cost"], row["Wb_Landing_Cost_Per_Landing"], row["Wb_Daily_Parking_Cost"]))
    airports_row.close()
    row_list = []
    row_list.append(["Iata_Code","Nb_Landing_Cost_Per_Landing","Nb_Daily_Parking_Cost","Wb_Landing_Cost_Per_Landing","Wb_Daily_Parking_Cost"])
    for airport in airports:
        row = []
        row.append(airport.iata_code)
        row.append(airport.nb_landing_cost)
        row.append(airport.nb_daily_parking_cost)
        row.append(airport.wb_landing_cost)
        row.append(airport.wb_daily_parking_cost)
        row_list.append(row)

    with open(files_dir+'structured_airports.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()

# ----------------- AIRCRAFT MODEL ----------------- #

class StructuredAircraftModel:
    def __init__(self, model, fleet, atc_avg_cost_naut_mile, maint_avg_cost_min, fuel_avg_cost_min, airp_handling_cost, mtow, cpt, opt, scb, ccb, cab):
        super().__init__()
        self.model = model
        self.fleet = fleet
        self.atc_avg_cost_naut_mile = atc_avg_cost_naut_mile
        self.maint_avg_cost_min = maint_avg_cost_min
        self.fuel_avg_cost_min = fuel_avg_cost_min
        self.airp_handling_cost = airp_handling_cost
        self.total_seats = 0
        self.economic_seats = 0
        self.business_seats = 0
        self.mtow = mtow
        self.cpt = cpt
        self.opt = opt
        self.scb = scb
        self.ccb = ccb
        self.cab = cab
    
    def __eq__(self, value):
        if hasattr(value, 'model'):
            return self.model == value.model
        else:    
            return self.model == value
    
    def add_business_seats(self, business_seats):
        if self.business_seats == 0:
            self.total_seats += business_seats
            self.business_seats = business_seats
        else:
            self.total_seats += business_seats - self.business_seats 
            self.business_seats = business_seats
        
    def add_economic_seats(self, economic_seats):
        if self.economic_seats == 0:
            self.total_seats += economic_seats
            self.economic_seats = economic_seats
        else:
            self.total_seats += economic_seats - self.economic_seats 
            self.economic_seats = economic_seats

def readAircraftModel(structured_aircraft_model):
    with open(files_dir+"aircraft_models.csv") as models_row:
        reader = csv.DictReader(models_row)
        for row in reader:
            structured_aircraft_model.append(StructuredAircraftModel(row["Model"], row["Fleet"], row["Atc_Avg_Cost_Naut_Mile"], row["Maint_Avg_Cost_Min"], row["Fuel_Avg_Cost_Min"], row["Airp_Handling_Cost"], row["MTOW"], row["CPT"], row["OPT"], row["SCB"], row["CCB"], row["CAB"]))
    models_row.close()

def writeAircraftModel(strcutured_aircraft_models):
    row_list = []
    row_list.append(["Model", "Fleet", "Atc_Avg_Cost_Naut_Mile", "Maint_Avg_Cost_Min", "Fuel_Avg_Cost_Min", "Airp_Handling_Cost", "MTOW", "CPT", "OPT", "SCB", "CCB", "CAB"])
    for aircraft_model in strcutured_aircraft_models:
        row = []
        row.append(aircraft_model.model)
        row.append(aircraft_model.fleet)
        row.append(aircraft_model.atc_avg_cost_naut_mile)
        row.append(aircraft_model.maint_avg_cost_min)
        row.append(aircraft_model.fuel_avg_cost_min)
        row.append(aircraft_model.airp_handling_cost)
        row.append(aircraft_model.mtow)
        row.append(aircraft_model.cpt)
        row.append(aircraft_model.opt)
        row.append(aircraft_model.scb)
        row.append(aircraft_model.ccb)
        row.append(aircraft_model.cab)
        row_list.append(row)
    with open(files_dir+"structured_aircraft_models.csv", 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()


def filterAicraftModel():
    aircraft_models_used = set()
    structured_aircraft_model = []
    with open(files_dir+"aircraft.csv") as aircraft_row:
        reader = csv.DictReader(aircraft_row)
        for row in reader:
            aircraft_models_used.update({row["Model"]})
    aircraft_row.close()
    readAircraftModel(structured_aircraft_model)
    structured_aircraft_model = list(filter(lambda x: x.model in aircraft_models_used, structured_aircraft_model))
    writeAircraftModel(structured_aircraft_model)


# --------------- AIRCRAFT --------------------#
# class StructuredAircraft:
#     def __init__(self):
        

# --------------- MAINTENANCES ----------------- #
class StructuredMaintenance:
    def __init__(self, plate, check_type, start_time, end_time, airport, status):
        super().__init__()
        self.plate = plate
        self.check_type = check_type
        self.start_time = datetime.strptime(start_time, "%d/%m/%Y %H:%M")
        self.end_time = datetime.strptime(end_time, "%d/%m/%Y %H:%M")
        self.airport = airport
        self.status = status

def getStructuredMaintenances():
    aircraft = []
    maintenances = []
    with open(files_dir+"aircraft.csv") as aircraft_row:
        reader = csv.DictReader(aircraft_row)
        for row in reader:
            aircraft.append(row["Plate"])
    aircraft_row.close()
    with open(files_dir+"unstructured_maintenances.csv") as maintenances_row:
        reader = csv.DictReader(maintenances_row)
        for row in reader:
            if row["Plate"] in aircraft:
                maintenances.append(StructuredMaintenance(row["Plate"], row["CheckType_Code"], row["Start_Time"], row["End_Time"], row["Airport"], row["Status"]))
    maintenances_row.close()
    row_list = []
    row_list.append(["Plate","CheckType_Code","Start_Time","End_Time","Airport","Status"])
    for maintenance in maintenances:
        row = []
        row.append(maintenance.plate)
        row.append(maintenance.check_type)
        row.append(maintenance.start_time.strftime("%d/%m/%Y %H:%M"))
        row.append(maintenance.end_time.strftime("%d/%m/%Y %H:%M"))
        row.append(maintenance.airport)
        row.append(maintenance.status)
        row_list.append(row)
        
    with open(files_dir+'structured_maintenances.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()


# ------------------- GENERAL FLIGHTS --------------------- #

class StructuredFlight:
    def __init__(self, flight, origin, destination, needed_seats, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold):
        super().__init__()
        self.flight = flight
        self.origin = origin
        self.destination = destination
        self.needed_seats = needed_seats
        self.start_time = datetime.strptime(start_time, "%m/%d/%Y %H:%M")
        self.end_time = datetime.strptime(end_time, "%m/%d/%Y %H:%M")
        self.business_seats = business_seats
        self.economic_seats = economic_seats
        self.business_seats_sold = business_seats_sold
        self.economic_seats_sold = economic_seats_sold


def readFlights(structured_flights):
    with open(files_dir+"unstructured_flights.csv") as flights_row:
        reader = csv.DictReader(flights_row)
        for row in reader:
           structured_flights.append(StructuredFlight(row["Flight"], row["Origin"], row["Destination"], row["Needed_Seats"], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"]))
    flights_row.close()

def writeStructuredFlights(structured_flights):
        row_list = []
        row_list.append(["Flight", "Origin", "Destination", "Needed_Seats", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold"])
        for flight in structured_flights:
            row = []
            row.append(flight.flight)
            row.append(flight.origin)
            row.append(flight.destination)
            row.append(flight.needed_seats)
            row.append(flight.start_time.strftime("%d/%m/%Y %H:%M"))
            row.append(flight.end_time.strftime("%d/%m/%Y %H:%M"))
            row.append(flight.business_seats)
            row.append(flight.economic_seats)
            row.append(flight.business_seats_sold)
            row.append(flight.economic_seats_sold)
            row_list.append(row)
        
        with open(files_dir+'structured_flights.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(row_list)


def getStructuredFlights():
    structured_flights = []
    readFlights(structured_flights)
    writeStructuredFlights(structured_flights)


# --------------------- MODEL FLIGHTS --------------------------- #

class StructuredModelFlight:
    def __init__(self, flight, origin, destination, aircraft_model, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, proper_date):
        super().__init__()
        self.flight = flight
        self.origin = origin
        self.destination = destination
        self.aircraft_model = aircraft_model
        if not proper_date:
            self.start_time = datetime.strptime(start_time, "%m/%d/%Y %H:%M")
            self.end_time = datetime.strptime(end_time, "%m/%d/%Y %H:%M")
        else:
            self.start_time = datetime.strptime(start_time, "%d/%m/%Y %H:%M")
            self.end_time = datetime.strptime(end_time, "%d/%m/%Y %H:%M")
        self.business_seats = business_seats
        self.economic_seats = economic_seats
        self.business_seats_sold = business_seats_sold
        self.economic_seats_sold = economic_seats_sold


def readModelFlights(strcutured_model_flights, proper_date):
    with open(files_dir+"model_flights.csv") as flights_row:
        reader = csv.DictReader(flights_row)
        for row in reader:
           strcutured_model_flights.append(StructuredModelFlight(row["Flight"], row["Origin"], row["Destination"], row["Aircraft_Model"], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], proper_date))
    flights_row.close()

def writeStructuredModelFlights(structured_model_flights):
        row_list = []
        row_list.append(["Flight", "Origin", "Destination", "Aircraft_Model", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold"])
        for flight in structured_model_flights:
            row = []
            row.append(flight.flight)
            row.append(flight.origin)
            row.append(flight.destination)
            row.append(flight.aircraft_model)
            row.append(flight.start_time.strftime("%d/%m/%Y %H:%M"))
            row.append(flight.end_time.strftime("%d/%m/%Y %H:%M"))
            row.append(flight.business_seats)
            row.append(flight.economic_seats)
            row.append(flight.business_seats_sold)
            row.append(flight.economic_seats_sold)
            row_list.append(row)
        
        with open(files_dir+'structured_model_flights.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(row_list)
        file.close()

def getStructuredModelFlights():
    structured_model_flights = []
    readModelFlights(structured_model_flights, False)
    writeStructuredModelFlights(structured_model_flights)


# -------------------- FLEET FLIGHTS -------------------- #
class StructuredFleetFlight:
    def __init__(self, flight, origin, destination, aircraft_fleet, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, proper_date):
        self.flight = flight
        self.origin = origin
        self.destination = destination
        self.aircraft_fleet = aircraft_fleet
        if not proper_date:
            self.start_time = datetime.strptime(start_time, "%m/%d/%Y %H:%M")
            self.end_time = datetime.strptime(end_time, "%m/%d/%Y %H:%M")
        else:
            self.start_time = datetime.strptime(start_time, "%d/%m/%Y %H:%M")
            self.end_time = datetime.strptime(end_time, "%d/%m/%Y %H:%M")
        self.business_seats = business_seats
        self.economic_seats = economic_seats
        self.business_seats_sold = business_seats_sold
        self.economic_seats_sold = economic_seats_sold
    
    def __eq__(self, other):
        return self.flight == other.flight

    def add_fleet(self, fleet):
        self.aircraft_fleet = fleet

def readUnstructuredFleetFlights(places_flights, proper_date):
    with open(files_dir+"unstructured_fleet_flights.csv") as flight_row:
        reader = csv.DictReader(flight_row)
        for row in reader:
            places_flights.append(StructuredFleetFlight(row["Flight"], row["Origin"], row["Destination"], None, row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], proper_date))
    flight_row.close()

def readStructuredFleetFlights(structured_fleet_flights, filename):
    with open(files_dir+filename) as flight_row:
        reader = csv.DictReader(flight_row)
        for row in reader:
            structured_fleet_flights.append(StructuredFleetFlight(row["Flight"], row["Origin"], row["Destination"], row["Aircraft_Fleet"], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], True))
    flight_row.close()


def writeStructuredModelToFleetFlights(structured_model_flights, strcutured_aircraft_model):
    row_list = []
    row_list.append(["Flight", "Origin", "Destination", "Aircraft_Fleet", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold"])
    for flight in structured_model_flights:
        row = []
        row.append(flight.flight)
        row.append(flight.origin)
        row.append(flight.destination)
        fleet = strcutured_aircraft_model[strcutured_aircraft_model.index(flight.aircraft_model)].fleet
        row.append(fleet)
        row.append(flight.start_time.strftime("%d/%m/%Y %H:%M"))
        row.append(flight.end_time.strftime("%d/%m/%Y %H:%M"))
        row.append(flight.business_seats)
        row.append(flight.economic_seats)
        row.append(flight.business_seats_sold)
        row.append(flight.economic_seats_sold)
        row_list.append(row)
    
    with open(files_dir+'structured_model_to_fleet_flights.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()

def writeStructuredFleetFlights(structured_fleet_flights):
    row_list = []
    row_list.append(["Flight", "Origin", "Destination", "Aircraft_Fleet", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold"])
    for flight in structured_fleet_flights:
        row = []
        row.append(flight.flight)
        row.append(flight.origin)
        row.append(flight.destination)
        row.append(flight.aircraft_fleet)
        row.append(flight.start_time.strftime("%d/%m/%Y %H:%M"))
        row.append(flight.end_time.strftime("%d/%m/%Y %H:%M"))
        row.append(flight.business_seats)
        row.append(flight.economic_seats)
        row.append(flight.business_seats_sold)
        row.append(flight.economic_seats_sold)
        row_list.append(row)
    
    with open(files_dir+'structured_fleet_flights.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(row_list)
    file.close()

def getStructuredFleetFlights():
    structured_model_flights = []
    structured_aircraft_model = []
    readModelFlights(structured_model_flights, True)
    readAircraftModel(structured_aircraft_model)
    writeStructuredModelToFleetFlights(structured_model_flights, structured_aircraft_model)

def getPlacesToFleetFlights(initial_proper_date):
    places_flights = []
    original_flights = []
    readUnstructuredFleetFlights(places_flights, initial_proper_date)
    readStructuredFleetFlights(original_flights, "original_fleet_flights.csv")
    for places_flight in places_flights:
        places_flight.add_fleet(original_flights[original_flights.index(places_flight)].aircraft_fleet)
    writeStructuredFleetFlights(places_flights)


# ------------ OTHER FLIGHT ANALYSIS --------------- #


class TempFlight:
    def __init__(self, origin, destination, aircraft_model):
        super().__init__()
        self.origin = origin
        self.destination = destination
        if int(aircraft_model) == 319 or int(aircraft_model) == 320 or int(aircraft_model) == 321:
            self.aircraft_fleet = 'NB'
        else:
            self.aircraft_fleet = 'WB'
    
    def __eq__(self, value):
        return self.origin == value.origin and self.destination == value.destination and self.aircraft_fleet == value.aircraft_fleet
    
    def __repr__(self):
        return ("{{Origin: {origin}, Destination: {destination}, Aircraft Fleet: {aircraft_fleet}\n}}").format(**vars(self))

def getDistinctFlights():
    flights = []
    airports = []
    with open(files_dir+"fleet_flights.csv") as flights_row:
        reader = csv.DictReader(flights_row)
        for row in reader:
            if not row["Origin"] in airports:
                airports.append(row["Origin"])
            if not row["Destination"] in airports:
                airports.append(row["Destination"])
            elem = TempFlight(row["Origin"], row["Destination"], row["Aircraft_Type"])
            if not elem in flights:
               flights.append(elem)
    flights_row.close()
    return airports

def filterFlights():
    models = []
    flights = []
    with open(files_dir+"aircraft_models.csv") as models_row:
        reader = csv.DictReader(models_row)
        for row in reader:
            models.append(StructuredAircraftModel(row["Model"], row["Fleet"], row["Atc_Avg_Cost_Naut_Mile"], row["Maint_Avg_Cost_Min"], row["Fuel_Avg_Cost_Min"], row["Airp_Handling_Cost"], row["MTOW"], row["CPT"], row["OPT"], row["SCB"], row["CCB"], row["CAB"]))
    models_row.close()
    with open(files_dir+"aircraft.csv") as aircraft_row:
        reader = csv.DictReader(aircraft_row)
        for row in reader:
            model = models[models.index(row["Model"])]
            if model.economic_seats < int(row["Economic_Seats"]):
                model.add_economic_seats(int(row["Economic_Seats"]))
            if model.business_seats < int(row["Business_Seats"]):
                model.add_business_seats(int(row["Business_Seats"]))
    aircraft_row.close()
    with open(files_dir+"model_flights_original.csv") as flights_row:
        reader = csv.DictReader(flights_row)
        for row in reader:
            model = models[models.index(row["Aircraft_Model"])]
            business_seats_sold = int(row["Business_Seats_Sold"])
            economic_seats_sold = int(row["Economic_Seats_Sold"])
            business_seats = int(row["Business_Seats"])
            economic_seats = int(row["Economic_Seats"])
            total_seats = business_seats+economic_seats
            if model.total_seats >= total_seats and model.business_seats >= business_seats and model.economic_seats >= economic_seats and business_seats_sold <= business_seats and economic_seats_sold <= economic_seats:
                flights.append(StructuredModelFlight(row["Flight"], row["Origin"], row["Destination"], row["Aircraft_Model"], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], True))
    flights_row.close()
    writeStructuredModelFlights(flights)


getPlacesToFleetFlights(True)
#getStructuredMaintenances()
#filterAicraftModel()
#getStructuredFleetFlights()
#filterCityPairs()
#filterFlights()
# getStructuredModelFlights()
#print(len(getDistinctFlights()))
#getStructuredMaintenances()
#getStructuredAirports("fleet_flights.csv", "maintenances.csv")
#filterCityPairs()