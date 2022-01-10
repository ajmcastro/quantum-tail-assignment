import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
import argparse
from Loader import read_data
import random
from models.AircraftModelFleet import AircraftFleet
from models.Activity import Maintenance
from scheduler.Solution import Solution
import pathlib
import csv
import datetime
import copy

NRDAYS = 30

def decision(probability):
    return random.random() < probability

def main():

    parser = argparse.ArgumentParser(description="""
    This script is going to create an efficient assignment for the Tail Assignment Problem 
    By default the problem is modeled as a BQM direclty using parameters for encouraging or disencouraging some assignments.
    The default formulation assumes that at least a valid situation exists (no extra flights are needed)
    """)
    parser.add_argument("--flights", type=int, help="Number of flights to be generated")
    # parser.add_argument("--aircraftpath", help="Path to the file that includes the aircraft to be considered when generating the flights")
    parser.add_argument("--aircraft", type=int, help="Number of aircraft to be generated")
    parser.add_argument("--filesdirectory", default="data/final/model3", help="Path to the folder of the csv data files. Don't forget to follow the names' specifications")
    parser.add_argument("--groupdata", action="store_true", help="Get a solution using grouped flights")
    parser.add_argument("--initialdate", default="01/09/2009 00:00", type=lambda d: datetime.datetime.strptime(d, "%d/%m/%Y %H:%M") , help="Initial date in the format dd/mm/yyyy hh:mm")
    parser.add_argument("--finaldate", default="30/09/2009 23:59", type=lambda d: datetime.datetime.strptime(d, "%d/%m/%Y %H:%M") , help="Final date in the format dd/mm/yyyy hh:mm")
    parser.add_argument("--ndays", type=int, help="Number of days to consider")

    args = parser.parse_args()


    _, _, aircraft, flights, _ = read_data(False, args.filesdirectory+"/", False, args.groupdata, args.initialdate, args.finaldate)
    print("F: ", len(flights))
    generatedata = GenerateData(flights, aircraft, args.flights, args.groupdata, args.ndays)
    if not args.flights and not args.aircraft:
        raise ValueError("You must specify the type of data you want to generate")
    if args.flights:
        generatedata.get_flights_on_city_pairs(args.flights)
    if args.aircraft:
        generatedata.get_nb_aircraft(args.aircraft)

class GenerateData:
    def __init__(self, flights, aircraft, num_flights, groupdata=False, ndays=0):
        self.original_flights = copy.copy(flights)
        self.flights = flights
        self.aircraft = aircraft
        self.groupdata = groupdata
        self.num_flights = num_flights
        self.ndays = ndays
        # if not ndays is None and ndays > 0:
        #     self.update_flights_on_days(ndays)
    
    def update_flights_on_days(self, ndays):
        count_days = {day: 0 for day in range(1,NRDAYS-(ndays-1))}
        for day in range(1,NRDAYS-(ndays-1)):

            initial_date = datetime.datetime.strptime(str(day)+"/09/2009 00:00", "%d/%m/%Y %H:%M")
            final_date = datetime.datetime.strptime(str(day+(ndays-1))+"/09/2009 23:59", "%d/%m/%Y %H:%M")
            
            for flight in self.original_flights:
                if flight.start_time >= initial_date and flight.end_time <= final_date:
                    count_days[day] += 1
        count_days = {k: v for k, v in sorted(count_days.items(), key=lambda item: item[1], reverse=True)}
        how_many = []
        for count_day in count_days:
            if count_days[count_day] > 2*self.num_flights:
                how_many.append(count_day)
        day_index = random.randint(0, len(how_many)-1)
        #day = next(iter(count_days))
        day = how_many[day_index]
        initial_date_ = datetime.datetime.strptime(str(day)+"/09/2009 00:00", "%d/%m/%Y %H:%M")
        final_date_ = datetime.datetime.strptime(str(day+(ndays-1))+"/09/2009 23:59", "%d/%m/%Y %H:%M")
        self.original_flights.sort()
        flights_temp = copy.copy(self.original_flights)
        for flight in self.original_flights:
            if flight.start_time < initial_date_ or flight.end_time > final_date_:
                flights_temp.remove(flight)

        self.flights = flights_temp
        print(len(self.flights))
        print("Initial: ", initial_date_)
        print("final: ", final_date_)
    
    def get_flights_on_destination(self, num_flights):
        final_flights = []
        destinations = {}
        destinations_flights = {}
        for flight in self.flights:
            if flight.destination.iata_code in destinations:
                destinations[flight.destination.iata_code] += 1
                destinations_flights[flight.destination.iata_code].append(flight)
            else:
                destinations.update({flight.destination.iata_code: 1})
                destinations_flights.update({flight.destination.iata_code: [flight]})

        for destination in destinations:
            destinations[destination] /= len(self.flights)
        print("Dest: ", destinations)

        for num in range(num_flights):    
            choosed_destination = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
            sum_prob = 0
            for destination in destinations:
                sum_prob += destinations[destination]
                if choosed_destination <= sum_prob:
                    flight_pos = random.randint(0, len(destinations_flights[destination])-1)
                    final_flights.append(destinations_flights[destination][flight_pos])
                    break
        print(final_flights)
    
    def add_maintenance(self, assignment, aircraft_index):
        aircraft_maintenances = self.aircraft[aircraft_index].maintenances
        for maintenance in aircraft_maintenances:
            if not maintenance in assignment[aircraft_index]: 
                if assignment[aircraft_index][len(assignment[aircraft_index])-1].end_time >= maintenance.start_time + datetime.timedelta(hours=1) and assignment[aircraft_index][len(assignment[aircraft_index])-1].start_time < maintenance.start_time:
                    assignment[aircraft_index].append(maintenance)

    def get_flights_on_city_pairs(self, num_flights):
        while True:
            if not self.ndays is None and self.ndays > 0:
                self.update_flights_on_days(self.ndays)
            assignment = [[] for i in range(len(self.aircraft))]
            not_working = [[] for i in range(len(self.aircraft))]
            final_flights = []
            pairs = {}
            pairs_flights = {}
            for flight in self.flights:
                if (flight.origin.iata_code, flight.destination.iata_code) in pairs:
                    pairs[(flight.origin.iata_code, flight.destination.iata_code)] += 1
                    pairs_flights[(flight.origin.iata_code, flight.destination.iata_code)].append(flight)
                else:
                    pairs.update({(flight.origin.iata_code, flight.destination.iata_code): 1})
                    pairs_flights.update({(flight.origin.iata_code, flight.destination.iata_code): [flight]})
            for pair in pairs:
                pairs[pair] /= len(self.flights)
            pairs = {k: v for k, v in sorted(pairs.items(), key=lambda item: item[1])}


            i = 0
            error_chosing = 0
            while i < num_flights:
                # assignment_max_size = max(list(map(lambda assig: len(assig), assignment)))
                # if assignment_max_size == len(self.flights):
                #     break
                print("I: ", i)
                empty = list(filter(lambda assig: len(assig) == 0, assignment))
                if len(empty) > 0:
                    chosen_destination_valid = False
                    while not chosen_destination_valid:
                        if error_chosing >= 70:
                            break
                        choosed_destination = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                        sum_prob = 0
                        for pair in pairs:
                            sum_prob += pairs[pair]
                            if choosed_destination <= sum_prob:
                                flight_pos = random.randint(0, len(pairs_flights[pair])-1)
                                final_flight = pairs_flights[pair][flight_pos]
                                delta = self.flights[len(self.flights)-1].start_time - self.flights[0].start_time
                                delta /= 5
                                data = self.flights[0].start_time + delta
                                if not final_flight in final_flights and final_flight.start_time <= data:
                                    chosen_destination_valid = True
                                else:
                                    error_chosing += 1
                                break
                    if error_chosing >= 70:
                        break
                    for aircraft_index, assign in enumerate(assignment):
                        if len(assign) > 0:
                            continue
                        aircraft = self.aircraft[aircraft_index]
                        if aircraft.can_perform_flight(final_flight):
                            assignment[aircraft_index].append(final_flight)
                            final_flights.append(final_flight)
                            self.add_maintenance(assignment, aircraft_index)
                            # if final_flight.origin == final_flight.destination:
                            #     i += 2
                            # else:
                            #     i += 1
                            # break
                            if self.verify_solution(final_flights, assignment):
                                if final_flight.origin == final_flight.destination:
                                    i += 2
                                else:
                                    i += 1
                                break
                            else:
                                if isinstance(assignment[aircraft_index][len(assignment[aircraft_index])-1], Maintenance):
                                    assignment[aircraft_index].pop()
                                assignment[aircraft_index].remove(final_flight)
                                final_flights.remove(final_flight)
                                not_working[aircraft_index].append(final_flight)
                else:
                    aircraft_index = random.randint(0, len(self.aircraft)-1)
                    prev_flight = assignment[aircraft_index][len(assignment[aircraft_index])-1]
                    pairs_ = {}
                    pairs_flights_ = {}
                    n_flights = 0
                    for pair in pairs:
                        if pair[0] == prev_flight.destination.iata_code:
                            pairs_flights_.update({pair: pairs_flights[pair]})
                            pairs_flights_[pair] = list(set(pairs_flights_[pair]) - set(final_flights))
                            pairs_flights_[pair] = list(set(pairs_flights_[pair]) - set(not_working[aircraft_index]))
                            if i == num_flights-1:
                                pairs_flights_[pair] = list(filter(lambda flight: self.aircraft[aircraft_index].can_perform_flight(flight) and not prev_flight.check_overlap(flight) and prev_flight.end_time < flight.start_time and prev_flight.end_time + datetime.timedelta(hours=24) >= flight.start_time and flight.origin != flight.destination, pairs_flights_[pair]))
                            else:
                                pairs_flights_[pair] = list(filter(lambda flight: self.aircraft[aircraft_index].can_perform_flight(flight) and not prev_flight.check_overlap(flight) and prev_flight.end_time < flight.start_time and prev_flight.end_time + datetime.timedelta(hours=24) >= flight.start_time, pairs_flights_[pair]))
                            if len(pairs_flights_[pair]) == 0:
                                del pairs_flights_[pair]
                            else:
                                pairs_.update({pair: len(pairs_flights_[pair])})
                                n_flights += len(pairs_flights_[pair])
                    
                    if n_flights == 0:
                        #print("Go BACK")
                        if isinstance(prev_flight, Maintenance):
                            assignment = [[] for i in range(len(self.aircraft))]
                            not_working = [[] for i in range(len(self.aircraft))]
                            final_flights = []
                            pairs = {}
                            pairs_flights = {}
                            i=0
                            continue
                        not_working[aircraft_index] = list(filter(lambda not_w: not_w.end_time < prev_flight.start_time, not_working[aircraft_index]))
                        not_working[aircraft_index].append(prev_flight)
                        assignment[aircraft_index].remove(prev_flight)
                        final_flights.remove(prev_flight)
                        if prev_flight.origin == prev_flight.destination:
                            i -= 2
                        else:
                            i -= 1
                        continue
                    # n_zeros = 0
                    for pair_ in pairs_:
                        pairs_[pair_] /= n_flights
                    #     if pairs_[pair_] == 0:
                    #         n_zeros += 1
                    pairs_ = {k: v for k, v in sorted(pairs_.items(), key=lambda item: item[1])}
                    
            #         # if n_zeros == len(pairs_):
            #         #     not_working[aircraft_index] = list(filter(lambda not_w: not_w.end_time < prev_flight.start_time, not_working[aircraft_index]))
            #         #     not_working[aircraft_index].append(prev_flight)
            #         #     assignment[aircraft_index].remove(prev_flight)
            #         #     i -= 1
            #         #     print("III: ", i)
            #         #     continue
                    
                    choosed_destination = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
                    sum_prob = 0
                    for pair_ in pairs_:
                        sum_prob += pairs_[pair_]
                        if choosed_destination <= sum_prob:
                            flight_pos = random.randint(0, len(pairs_flights_[pair_])-1)
                            final_flight = pairs_flights_[pair_][flight_pos]
                            #print("Prev FLIGHT: ", prev_flight.original_flight_index, " FINAL FLIGHt: " ,final_flight.original_flight_index)
                            break
                    assignment[aircraft_index].append(final_flight)
                    assignment[aircraft_index].sort()
                    final_flights.append(final_flight)
                    final_flights.sort()
                    self.add_maintenance(assignment, aircraft_index)
                    # if final_flight.origin == final_flight.destination:
                    #     i += 2
                    # else:
                    #     i += 1
                    if self.verify_solution(final_flights, assignment):
                        if final_flight.origin == final_flight.destination:
                            i += 2
                        else:
                            i += 1
                        continue
                    else:
                        if isinstance(assignment[aircraft_index][len(assignment[aircraft_index])-1], Maintenance):
                            assignment[aircraft_index].pop()
                        assignment[aircraft_index].remove(final_flight)
                        final_flights.remove(final_flight)
                        not_working[aircraft_index].append(final_flight)

            if error_chosing >= 70:
                error_chosing = 0
                continue               
            for aircraft_index, aircraft in enumerate(self.aircraft):
                maintenances = aircraft.maintenances
                for maintenance in maintenances:
                    if not maintenance in assignment[aircraft_index]:
                        assignment[aircraft_index].append(maintenance)
                assignment[aircraft_index].sort()
                #print(assignment[aircraft_index])
            if self.verify_solution(final_flights, assignment):
                self.export('flight', final_flights)
                self.export('flight', final_flights, own=False)
                break
    
    def verify_solution(self, final_flights, assignment):
        final_flights.sort()
        for index, _ in enumerate(assignment):
           assignment[index].sort()
        sol = Solution(flights = final_flights, aircraft=self.aircraft, solution=assignment, is_complete = True)
        return sol.verify()


    
    def get_nb_aircraft(self, num_aircraft):
        final_aircraft = []
        models = {}
        models_aircraft = {}
        sum_aircraft = 0
        for aircraft in self.aircraft:
            if aircraft.model.fleet == AircraftFleet.NB and aircraft.model.model in models:
                models[aircraft.model.model] += 1
                models_aircraft[aircraft.model.model].append(aircraft)
                sum_aircraft += 1
            elif aircraft.model.fleet == AircraftFleet.NB:
                models.update({aircraft.model.model: 1})
                models_aircraft.update({aircraft.model.model: [aircraft]})
                sum_aircraft += 1

        for model in models:
            models[model] /= sum_aircraft
        print("Dest: ", models)

        for num in range(num_aircraft):    
            choosed_destination = int.from_bytes(os.urandom(8), byteorder="big") / ((1 << 64) - 1)
            sum_prob = 0
            for model in models:
                sum_prob += models[model]
                if choosed_destination <= sum_prob:
                    flight_pos = random.randint(0, len(models_aircraft[model])-1)
                    final_aircraft.append(models_aircraft[model][flight_pos])
                    break
        self.export('aircraft', final_aircraft)
    
    def export(self, data_type, data, own=True):
        if data_type == 'flight':
            data.sort()
            row_list = []
            if own:
                if self.groupdata:
                    header = ["Flight", "Origin", "Destination", "Aircraft_Fleet", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold", "Distance", "Cost_319", "Cost_320", "Cost_321", "Composed_Flights"]
                    row_list.append(header)
                else:
                    row_list.append(["Flight", "Origin", "Destination", "Aircraft_Fleet", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold"])
            else:
                row_list.append(["Voo", "Origem", "Destino", "Configuracao", "Partida", "Chegada", "Lugares_Executiva", "Lugares_Economica", "Lugares_Exec_Vendidos", "Lugares_Econ_Vendidos"])
            for flight in data:
                if own and self.groupdata:
                    row_list.append(flight.csv_repr())
                else:
                    row = []
                    row.append(flight.number)
                    row.append(flight.origin.iata_code)
                    row.append(flight.destination.iata_code)
                    if own:
                        if flight.aircraft_fleet == AircraftFleet.NB:
                            row.append('NB')
                        else:
                            row.append('WB')
                    else:
                        row.append(str(flight.business_seats+flight.economic_seats))
                    row.append(flight.start_time.strftime("%d/%m/%Y %H:%M"))
                    row.append(flight.end_time.strftime("%d/%m/%Y %H:%M"))
                    row.append(flight.business_seats)
                    row.append(flight.economic_seats)
                    row.append(flight.business_seats_sold)
                    row.append(flight.economic_seats_sold)
                    row_list.append(row)
            foldername = 'data/generated/maintenances/'+str(len(self.aircraft))+'_aircraft'+'/'+str(len(data))+"_"+data_type
            pathlib.Path(foldername).mkdir(parents=True, exist_ok=True) 
            filename = 'data/generated/maintenances/{aircraft_len}_aircraft/{num}_{data_type}/{own}-{data_type}-{num}-{date:%Y-%m-%d_%H:%M:%S}.csv'.format( date=datetime.datetime.now(), data_type=data_type, num = len(data), own=own, aircraft_len = len(self.aircraft) )
        else:
            row_list = []
            row_list.append(["Plate", "Name", "Model", "Total_Seats", "Business_Seats", "Economic_Seats"])
            for aircraft in data:
                row = []
                row.append(aircraft.plate)
                row.append(aircraft.name)
                row.append(aircraft.model.model)
                row.append(aircraft.total_seats)
                row.append(aircraft.business_seats)
                row.append(aircraft.economic_seats)
                row_list.append(row)
            foldername = 'data/generated/maintenances/'+str(len(data))+"_"+data_type
            pathlib.Path(foldername).mkdir(parents=True, exist_ok=True) 
            filename = 'data/generated/maintenances/{num}_{data_type}/{own}-{data_type}-{num}-{date:%Y-%m-%d_%H:%M:%S}.csv'.format( date=datetime.datetime.now(), data_type=data_type, num = len(data), own=own )
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(row_list)
        file.close()


        


if __name__ == "__main__":
    main()
