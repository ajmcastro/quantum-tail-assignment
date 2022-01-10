import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
import argparse
from models.utils.Graph import Graph
from datetime import datetime
from models.Aircraft import AircraftModel
from models.AircraftModelFleet import AircraftFleet
from models.Activity import ComposedFlight
from Loader import read_data
import csv

def main():
    parser = argparse.ArgumentParser(description="""
    This script is going to create an efficient assignment for the Tail Assignment Problem 
    By default the problem is modeled as a BQM direclty using parameters for encouraging or disencouraging some assignments.
    The default formulation assumes that at least a valid situation exists (no extra flights are needed)
    """)
    parser.add_argument("--aircraftmodel", action='store_true', help="Do assignment considering a pre-assigned aircraft model instead of a pre-assigned aircraft fleet")
    parser.add_argument("--filesdirectory", default="data/final/model3", help="Path to the folder of the csv data files. Don't forget to follow the names' specifications")
    parser.add_argument('--hubs', nargs='+')
    #parser.add_argument('--export', action='store_true')

    args = parser.parse_args()

    if len(args.hubs) == 0:
        raise ValueError("A list of Hubs must be provided in order to group flights")

    airports, aircraft_models, aircraft, flights, maintenances = read_data(args.aircraftmodel, args.filesdirectory+"/", False, False)
    groupdata = GroupData(flights, airports, aircraft_models, args.aircraftmodel, args.hubs)
    final_flights = groupdata.calculate_flights()
    groupdata.export_grouped_flights(final_flights, args.filesdirectory+"/")


class GroupData:
    def __init__(self, flights, airports, aircraft_models, has_aircraft_model, hubs=[]):
       self.flights = flights
       self.airports = airports
       self.hubs = list(map(lambda hub: airports[airports.index(hub)], hubs))
       self.aircraft_models = aircraft_models
       self.has_aircraft_model = has_aircraft_model
       self.flights_graph, self.hub_origin_flights, self.hub_destination_flights = self.create_flights_graph()
    
    def create_flights_graph(self):
        flights_graph = Graph(len(self.flights)) # graph of flights and connections between them
        temp_edges = [0]* len(self.flights)
        hub_origin_flights = []
        hub_destination_flights = []
        for flight1 in self.flights[:len(self.flights)-1]:
            if flight1.origin in self.hubs:
                hub_origin_flights.append(flight1.flight_index)
            if flight1.destination in self.hubs:
                hub_destination_flights.append(flight1.flight_index)
            for flight2 in self.flights[flight1.flight_index+1:]:
                if flight1.compatible_flight(flight2):
                    if not flight1.check_overlap(flight2):
                        if flight1.destination == flight2.origin:
                            flights_graph.add_edge(flight1.flight_index, flight2.flight_index)  # add edge between flghts that can be consecutive
                            temp_edges[flight1.flight_index] += 1
                            temp_edges[flight2.flight_index] += 1
        if self.flights[len(self.flights)-1].origin in self.hubs:
            hub_origin_flights.append(self.flights[len(self.flights)-1].flight_index)
        if self.flights[len(self.flights)-1].destination in self.hubs:
            hub_destination_flights.append(self.flights[len(self.flights)-1].flight_index)
        hub_origin_flights.sort()
        hub_destination_flights.sort()
        for index, i in enumerate(temp_edges):  # add nodes that have no connection to graph to be considered for the not reachable sets
            if i == 0:
                flights_graph.add_edge(index, index)
        hub_origin_flights.sort()
        hub_destination_flights.sort()
        return flights_graph, hub_origin_flights, hub_destination_flights
    
    def get_grouped_flights(self):
        self.merges = []
        removed = []
        print("Initial: ",len(self.flights))
        if len(self.hub_origin_flights) == 0 or len(self.hub_destination_flights) == 0:
            print("No possible to group with the given hub spots")
        
        total_reach, total_not_reach = self.flights_graph.get_all()

        # if self.hub_destination_flights[len(self.hub_destination_flights)-1] < self.flights[len(self.flights)-1].flight_index:
        #     final =  self.flights[self.hub_destination_flights[len(self.hub_destination_flights)-1]+1]
        # else:
        #     final = None
        # del self.flights[:self.hub_origin_flights[0]]
        # print("AA: ", self.hub_origin_flights[0])
        # if not final is None:
        #     del self.flights[self.flights.index(final):]
        # airports_values = []
        # for airport in self.airports:
        #     if not airport in hubs:
        #         airports_values.append({airport.iata_code: None})
        # for flight in self.flights:
        #     if not flight.origin in self.hubs:
        #         if airports_values is None:
        #             continue
        #         else:
        paths = {index: None for index in range(len(self.flights))}
        final_paths = []
        to_remove = []
        for middle_flight, flight in enumerate(self.flights):
            if middle_flight in removed:
                continue
            if not flight.origin in self.hubs:
                arrive_to = self.flights_graph.get_arrive_to(middle_flight)
                print(len(arrive_to))
                if not arrive_to is None:
                    if len(arrive_to) == 1:
                        removed.append(arrive_to[0])
                        #removed.append(middle_flight)
                        self.flights_graph.remove_vertice(arrive_to[0])
                        #self.flights_graph.remove_vertice(middle_flight)
                        print("Removed: ", arrive_to[0])
                        paths.update({arrive_to[0]: flight})
                    # if len(arrive_to) >= 1:
                    #     flights_ = list(map(lambda fi: self.flights[fi], arrive_to))
                    #     flights_.sort()
                    #     for arrive in flights_:
                    #         if arrive.origin == flight.destination and (arrive.origin in self.hubs or arrive.origin.iata_code == 'FNC'):
                    #             removed.append(arrive.original_flight_index)
                    #             removed.append(flight.original_flight_index)
                    #             self.flights_graph.remove_vertice(arrive.original_flight_index)
                    #             self.flights_graph.remove_vertice(flight.original_flight_index)
                    #             print("Removed: ", arrive.original_flight_index)
                    #             paths.update({arrive.original_flight_index: flight})
                    #             break
        for path in paths:
            next_flight = paths[path]
            if not next_flight is None:
                for final_path_index, final_path in enumerate(final_paths):
                    if self.flights[path] in final_path:
                        final_paths[final_path_index].append(next_flight)
                        break
                else:
                    final_paths.append([self.flights[path], next_flight])
        
        indexes = []
        for final_path in final_paths:
            print("AGGREGATED: ", list(map(lambda elem: "I: " +str(elem.original_flight_index)+ " OR: "+elem.origin.iata_code + " DEST: " + elem.destination.iata_code, final_path)))
            for flight in final_path:
                self.flights.remove(flight)
                indexes.append(flight.original_flight_index)
        self.merges = final_paths
        print("TOTAL: ", len(self.flights)+len(final_paths))
        print(indexes)
                

        # for origin_flight in self.hub_origin_flights:
        #     if origin_flight in removed:
        #         continue
        #     flight = self.flights[origin_flight]
        #     if flight.destination in self.hubs:
        #         self.merges.append([flight])
        #         self.flights_graph.remove_vertice(origin_flight)
        #         removed.append(origin_flight)
        #         continue
        #     adj = self.flights_graph.get_adj(origin_flight)
        #     merge = []
        #     while adj != None and len(adj) > 0:
        #         adj.sort(key = lambda x: self.flights[x].start_time)
        #         merge.append(adj[0])
        #         if self.flights[adj[0]].destination in self.hubs:
        #             break
        #         else:
        #             adj = self.flights_graph.get_adj(adj[0])
        #         # final = False
        #         # for adj_ in adj:
        #         #     if self.flights[adj_].destination in self.hubs:
        #         #         merge.append(adj_)
        #         #         final = True
        #         #         break
        #         # if not final:
        #         #     merge.append(adj[0])
        #         #     adj = self.flights_graph.get_adj(adj[0])
        #         # else:
        #         #     break
        #     if len(merge) > 0 and self.flights[merge[len(merge)-1]].destination in self.hubs:
        #         self.merges.append([flight] + list(map(lambda index: self.flights[index], merge)))
        #         for merge_i in merge:
        #             self.flights_graph.remove_vertice(merge_i)
        #             removed.append(merge_i)
        #         self.flights_graph.remove_vertice(origin_flight)
        #         removed.append(origin_flight)
        # final_flights = []
        # for merge1 in self.merges:
        #     for merge2 in merge1:
        #         print(merge2)
        #         self.flights.remove(merge2)
        #print(list(map(lambda flight: flight.original_flight_index+2, self.flights)))
        print("OUT: ", len(self.flights))


    def calculate_flights(self):
        self.get_grouped_flights()
        removed = self.flights
        to_merge = self.merges
        to_merge += list(map(lambda flight: [flight], self.flights ))
        final_flights = []
        i = 0
        total = 0
        for merge in to_merge:
            total += len(merge)
            merge.sort()
            costs = {}
            for model in self.aircraft_models:
                costs.update({model.model: model.get_operational_cost(merge)})
            origin = merge[0].origin
            destination = merge[len(merge)-1].destination
            start_time = merge[0].start_time
            end_time = merge[len(merge)-1].end_time
            max_seats = 0
            business_seats = 0
            economic_seats = 0
            business_seats_sold = 0
            economic_seats_sold = 0
            number = ""
            model_fleet = AircraftFleet.NB
            flights = ""
            distance = 0
            for index, merge2 in enumerate(merge):
                distance += merge2.flight_distance
                total_seats = merge2.business_seats + merge2.economic_seats
                if merge2.aircraft_fleet.value > model_fleet.value:
                    model_fleet = merge2.aircraft_fleet
                if total_seats > max_seats:
                    max_seats = total_seats
                    business_seats = merge2.business_seats
                    economic_seats = merge2.economic_seats
                    business_seats_sold = merge2.business_seats_sold
                    economic_seats_sold = merge2.economic_seats_sold
                if index < len(merge)-1:
                    number += str(merge2.number) + "-"
                    flights += str(merge2.original_flight_index) + "-"
            number += str(merge[len(merge)-1].number)
            flights += str(merge[len(merge)-1].original_flight_index)
            if self.has_aircraft_model:
                model_fleet = merge[0].aircraft_model
            composed_flight = ComposedFlight(i, i, number, origin, destination, model_fleet, start_time, end_time, business_seats, economic_seats, business_seats_sold, economic_seats_sold, distance, self.has_aircraft_model, costs, flights)
            final_flights.append(composed_flight)
        #print(total)
        return final_flights
    
    def export_grouped_flights(self, grouped_flights, export_directory):
        row_list = []
        header = ["Flight", "Origin", "Destination", "Aircraft_Fleet", "Start_Time", "End_Time", "Business_Seats", "Economic_Seats", "Business_Seats_Sold", "Economic_Seats_Sold", "Distance"]
        for model in self.aircraft_models:
            header.append("Cost_"+model.model)
        header.append("Composed_Flights")
        row_list.append(header)
        for flight in grouped_flights:
            row_list.append(flight.csv_repr())
        
        with open(export_directory+'grouped_flights4.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(row_list)
        file.close()


if __name__ == "__main__":
    main()