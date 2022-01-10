import csv
import scheduler.GenericMacros as macros
from models.CityPair import CityPair
from models.Airport import Airport
from models.AircraftModelFleet import AircraftModel
from models.Aircraft import Aircraft
from models.Activity import Flight, ComposedFlight, Maintenance
from datetime import datetime

activity_index = 0

def read_data(has_aircraft_model, files_dir, has_initial_solution, is_group_data, initial_date=None, final_date=None):
    airports = []
    aircraft_models = []
    aircraft = []
    flights = []
    maintenances = []
    airports = read_airports(files_dir)
    city_pairs = read_city_pairs(airports, files_dir)    
    aircraft_models = read_aircraft_models(files_dir)
    aircraft = read_aircraft(aircraft_models, files_dir)
    try:
        maintenances = read_maintenances(airports, aircraft, has_aircraft_model, files_dir, initial_date, final_date)
    except:
        pass
    if has_initial_solution:
        initial_solution = read_initial_solution(airports, aircraft, maintenances, files_dir)
    if not is_group_data:
        flights = read_flights(airports, aircraft_models, city_pairs, has_aircraft_model, files_dir, initial_date, final_date)
    else:
        flights = read_grouped_flights(airports, aircraft_models, city_pairs, has_aircraft_model, files_dir, initial_date, final_date)
    reorder_data(flights, maintenances)
    if has_initial_solution:
        return airports, aircraft_models, aircraft, flights, maintenances, initial_solution
    else:
        return airports, aircraft_models, aircraft, flights, maintenances

def read_airports(files_dir):
    airports = []
    with open(files_dir+"airports.csv") as airports_row:
        reader = csv.DictReader(airports_row)
        for row in reader:
            airports.append(Airport(row["Iata_Code"], row["Nb_Landing_Cost_Per_Landing"], row["Nb_Daily_Parking_Cost"], row["Wb_Landing_Cost_Per_Landing"], row["Wb_Daily_Parking_Cost"]))
    airports_row.close()
    return airports


def read_city_pairs(airports, files_dir):
    city_pairs = []
    with open(files_dir+"city_pairs.csv") as city_pairs_row:
        reader = csv.DictReader(city_pairs_row)
        for row in reader:
            city_pairs.append(CityPair(airports[airports.index(row["Origin"])], airports[airports.index(row["Destination"])], row["Distance_In_Nautical_Miles"]))
    city_pairs_row.close()
    return city_pairs

def read_aircraft_models(files_dir):
    aircraft_models = []
    with open(files_dir+"aircraft_models.csv") as aircraft_models_row:
        reader = csv.DictReader(aircraft_models_row)
        for row in reader:
            aircraft_models.append(AircraftModel(row["Model"], row["Fleet"], row["Atc_Avg_Cost_Naut_Mile"], row["Maint_Avg_Cost_Min"], row["Fuel_Avg_Cost_Min"], row["Airp_Handling_Cost"]))
    aircraft_models_row.close()
    return aircraft_models

def read_aircraft(aircraft_models, files_dir):
    aircraft_index = 0
    aircraft = []
    with open(files_dir+"aircraft.csv") as aircraft_row:
        reader = csv.DictReader(aircraft_row)
        for row in reader:
            aircraft.append(Aircraft(aircraft_index, row["Plate"], row["Name"], aircraft_models[aircraft_models.index(row["Model"])], row["Business_Seats"], row["Economic_Seats"]))
            aircraft_index += 1
    aircraft_row.close()
    return aircraft


def read_flights(airports, aircraft_models, city_pairs, has_aircraft_model, files_dir, initial_date = None, final_date = None):
    global activity_index
    flight_index = 0
    flights = []
    if has_aircraft_model:
        with open(files_dir+"model_flights.csv") as flights_row:
            reader = csv.DictReader(flights_row)
            for row in reader:
                if (initial_date is None or (not initial_date is None and datetime.strptime(row["Start_Time"], "%d/%m/%Y %H:%M") >= initial_date and datetime.strptime(row["End_Time"], "%d/%m/%Y %H:%M") <= final_date)):
                    flight = Flight(activity_index, flight_index, row["Flight"], airports[airports.index(row["Origin"])], airports[airports.index(row["Destination"])], aircraft_models[aircraft_models.index(row["Aircraft_Model"])], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], city_pairs[city_pairs.index(CityPair(row["Origin"], row["Destination"]))].distance, True)
                    flights.append(flight)
                    activity_index += 1
                    flight_index += 1
        flights_row.close()
    else:
        with open(files_dir+"fleet_flights.csv") as flights_row:
            reader = csv.DictReader(flights_row)
            for row in reader:
                if (initial_date is None or (not initial_date is None and datetime.strptime(row["Start_Time"], "%d/%m/%Y %H:%M") >= initial_date and datetime.strptime(row["End_Time"], "%d/%m/%Y %H:%M") <= final_date)):
                    flight = Flight(activity_index, flight_index, row["Flight"], airports[airports.index(row["Origin"])], airports[airports.index(row["Destination"])], row["Aircraft_Fleet"], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], city_pairs[city_pairs.index(CityPair(row["Origin"], row["Destination"]))].distance, False)
                    flights.append(flight)
                    activity_index += 1
                    flight_index += 1
        flights_row.close()
    return flights

def read_grouped_flights(airports, aircraft_models, city_pairs, has_aircraft_model, files_dir, initial_date=None, final_date=None):
    global activity_index
    flight_index = 0
    flights = []
    if has_aircraft_model:
        with open(files_dir+"grouped_model_flights.csv") as flights_row:
            reader = csv.DictReader(flights_row)
            for row in reader:
                if (initial_date is None or (not initial_date is None and datetime.strptime(row["Start_Time"], "%d/%m/%Y %H:%M") >= initial_date and datetime.strptime(row["End_Time"], "%d/%m/%Y %H:%M") <= final_date)):
                    flight = Flight(activity_index, flight_index, row["Flight"], airports[airports.index(row["Origin"])], airports[airports.index(row["Destination"])], aircraft_models[aircraft_models.index(row["Aircraft_Model"])], row["Start_Time"], row["End_Time"], row["Business_Seats"], row["Economic_Seats"], row["Business_Seats_Sold"], row["Economic_Seats_Sold"], city_pairs[city_pairs.index(CityPair(row["Origin"], row["Destination"]))].distance, True)
                    flights.append(flight)
                    activity_index += 1
                    flight_index += 1
        flights_row.close()
    else:
        with open(files_dir+"grouped_fleet_flights.csv") as flights_row:
            reader = csv.DictReader(flights_row)
            for row in reader:
                if (initial_date is None or (not initial_date is None and datetime.strptime(row["Start_Time"], "%d/%m/%Y %H:%M") >= initial_date and datetime.strptime(row["End_Time"], "%d/%m/%Y %H:%M") <= final_date)):
                    composed_flights = row.popitem()[1]
                    costs = {}
                    while True:
                        elem = row.popitem()
                        if elem[0] == 'Distance':
                            distance = elem[1]
                            break
                        else:
                            aircraft_model = elem[0].split('_')[1]
                            cost = elem[1]
                            costs.update({aircraft_model: float(cost)})
                    number = row["Flight"]
                    origin = airports[airports.index(row["Origin"])]
                    destination = airports[airports.index(row["Destination"])]
                    fleet = row["Aircraft_Fleet"]
                    start_time = row["Start_Time"]
                    end_time = row["End_Time"]
                    business_seats = row["Business_Seats"]
                    economic_seats = row["Economic_Seats"]
                    business_seats_sold = row["Business_Seats_Sold"]
                    economic_seats_sold = row["Economic_Seats_Sold"]
                    flight = ComposedFlight(activity_index, flight_index, number, origin, destination, row["Aircraft_Fleet"], start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, distance, False, costs, composed_flights)
                    flights.append(flight)
                    activity_index += 1
                    flight_index += 1
        flights_row.close()
    return flights

def read_maintenances(airports, aircraft, has_aircraft_model, files_dir, initial_date=None, final_date=None):
    global activity_index
    maintenance_index = 0
    maintenances = []
    with open(files_dir+"maintenances.csv") as maintenances_row:
        reader = csv.DictReader(maintenances_row)
        for row in reader:
            if row["CheckType_Code"] in macros.MAINTENANCE_TYPES:
                if (initial_date is None or(not initial_date is None and datetime.strptime(row["Start_Time"], "%d/%m/%Y %H:%M") >= initial_date and datetime.strptime(row["End_Time"], "%d/%m/%Y %H:%M") <= final_date)):
                    maintenance = Maintenance(activity_index, maintenance_index, row["CheckType_Code"], row["Start_Time"], row["End_Time"], airports[airports.index(row["Airport"])], row["Status"], has_aircraft_model)
                    aircraft[aircraft.index(row["Plate"])].add_maintenance(maintenance)
                    maintenance_index += 1
                    activity_index+=1
    maintenances_row.close()
    for aircraft_ref in aircraft:
        aircraft_ref.group_maintenances()
        maintenances += aircraft_ref.maintenances   
    return maintenances
      


def read_initial_solution(airports, aircraft, maintenances, files_dir):
    solution = [[] for i in range(len(aircraft))]
    flights = []
    with open(files_dir+"initial_solution.csv", "r") as aircraft_assignment:
        reader = csv.reader(aircraft_assignment, delimiter=",")
        next(reader, None) # ignore header
        for assignment in reader:
            aircraft_index = aircraft.index(assignment[0])
            for activity_assignment in assignment[1:]:
                if str(activity_assignment)[0] == 'F':
                    flight_index = int(str(activity_assignment)[3:])-1
                    solution[aircraft_index].append(flight_index)
                    flights.append(flight_index)
    return solution

def reorder_data(flights, maintenances):
    activities = [*flights, *maintenances]
    activities.sort()
    for index, activity in enumerate(activities):
        activity.set_original_index(index)