from models.Activity import Maintenance, Flight
from models.utils.Graph import Graph
from models.Aircraft import AircraftFleet
import scheduler.GenericMacros as macros
import copy
from itertools import combinations

class Scheduler:

    def __init__(self, flights, aircraft, aircraft_models, has_aircraft_model):
        self.flights = flights #previously ordered
        self.aircraft = aircraft
        self.aircraft_models = aircraft_models
        self.has_aircraft_model = has_aircraft_model
        self.flights_graph = None
        self.total_not_reach_by_aircraft = [[] for i in range(len(self.aircraft))] # [[[int]]] -- list of matrices where for each flight (row) there's a list of indexes of flights that are not reached from it (columns). Each matrix represents the not_reached flights for each aircraft
        self.overlap_flights = None
        self.or_aux_variables = []
        self.xor_aux_variables = []
        self.overlap_flights, self.total_not_reach_by_aircraft

    def pre_analysis_and_constraints(self):
        self.fill_maintenances_connections_and_overlaps()

    
    def get_flights_connections_and_overlaps(self):
        """
        Get pairs of flights that overlap and therefore cannot happen for the same aircraft as well as filling the flights_graph variable with the possible connections flights

        Note: flights_graph will be filled using flights indexes and not flights as the graph strucutuere is prepared just for numbers

        Returns:
            list -- List of pairs of flights that overlap
        """

        overlap_flights = []   # which flights overlap
        temp_edges = [0]* len(self.flights)
        self.flights_graph = Graph(len(self.flights)) # graph of flights and connections between them
        for flight1 in self.flights[:len(self.flights)-1]:
            for flight2 in self.flights[flight1.flight_index+1:]:
                if flight1.compatible_flight(flight2):
                    if flight1.check_overlap(flight2):
                        overlap_flights.append((flight1, flight2))
                    else:
                        if flight1.destination == flight2.origin:
                            self.flights_graph.add_edge(flight1.flight_index, flight2.flight_index)  # add edge between flghts that can be consecutive
                            temp_edges[flight1.flight_index] += 1
                            temp_edges[flight2.flight_index] += 1
        for index, i in enumerate(temp_edges):  # add nodes that have no connection to graph to be considered for the not reachable sets
            if i == 0:
                self.flights_graph.add_edge(index, index)
        self.overlap_flights = overlap_flights
        return overlap_flights
    
    def fill_maintenances_connections_and_overlaps(self):
        """
        For each aircraft set the flights that overlap aircraft's maintenances as well as the ones that can direclty connect before and after each obligatory maintenance. 
        """
        for aircraft in self.aircraft:
            for flight in self.flights:
                if aircraft.is_flight_compatible(flight) and not aircraft.is_flight_impossible_on_restrictions(flight):
                    if aircraft.is_flight_overlapping_maintenance(flight):
                        aircraft.add_overlap_flight(flight)
                    else:
                        aircraft.add_maintenance_connection_flight(flight)

    def get_aircraft_flights_compatibility(self):
        """
        For each model/fleet get a list of flights' indexes that may generally be operated by aircraft of that model/fleet. When flights have a pre-assigned model then the index of that flight will appear as compatible for the specific model and incompatible for all the other models. For the case of flights with just a pre-defined fleet it will set as  incomaptible the flights that require a WB aircraft and therefore are incomaptible to be operated by NB aircraft (WB aircrfat are compatible with all fllights as they can operate flights that require a smaller fleet) 

        Returns:
            dict -- For then case of flights with pre-defined aicraft_model: one dict where for each aircraft model name, there's a list of flights' indexes that may be operated by aircraft that belong to that model. For the case of pre-defined fleet: one array with the flights' indexes that may be operated by both WB and NB aircraft.
            set -- For then case of flights with pre-defined aicraft_model: one dict where for each aircraft model name, there's a set of flights' indexes that cannot be operated by aircraft that belong to that model. For the case of pre-defined fleet: one set with the flights' indexes that cannot be operated by NB aircraft, as all flights can be operated by WB aircraft.
        """
        if self.has_aircraft_model:
            flights_incompatible = {model.model: set() for model in self.aircraft_models}
            flights_compatible = {model.model: [] for model in self.aircraft_models} 
            for model in self.aircraft_models:        #calculate flights incompatible with each aircraft
                for flight in self.flights:
                    if flight.aircraft_model != model.model:
                        flights_incompatible[model.model].update({flight.flight_index})
                    else:
                        flights_compatible[model.model].append(flight.flight_index)
        else:
            flights_incompatible = set() #flights that require a WB aircraft and therefore are not compatible with a NB aircraft
            flights_compatible = [] #flights that can be operated by both WB and NB
            for flight in self.flights:
                if flight.aircraft_fleet == AircraftFleet.WB:
                    flights_incompatible.update({flight.flight_index})
                else:
                    flights_compatible.append(flight.flight_index)
        
        return flights_compatible, flights_incompatible

    



    def get_not_allowed_flights_by_aircraft(self, aircraft, flights_compatible, flights_incompatible, relaxed=False):
        """
        For a fiven aircraft and group of compatible and not compatible flights return the flights's indexes  of the flights that are not allowed to be performed by the given aircraft

        Arguments:
            aircraft {Aircraft} -- Aircraft to be analysed
            flights_compatible {list} -- List of flights that are compatible with the given aircraft (model/fleet and have enough space)
            flights_incompatible {set} -- Set of flights that are not compatible with the given aircraft (model/fleet don't match or have not enough space)

        Returns:
            set -- flights' indexes that are not allowed to be performed by the aircraft. Usually it will be the flights that are not compatible with the aircraft together witht the flights that overlap maintenances of the aircraft or are impossible to be operated by the aircraft due to other restrictions
        """
        not_allowed_flights = set()
        if self.has_aircraft_model:
            not_allowed_flights.update(flights_incompatible[aircraft.model.model]) #remove nodes that are not from the same aircraft model
            not_allowed_flights.update(set(filter(lambda flight_index: not aircraft.can_perform_flight(self.flights[flight_index]), flights_compatible[aircraft.model.model])))  #remove nodes that, although being from the same model, can not be performed by aircraft due to few seats available
        else:
            if aircraft.model.fleet == AircraftFleet.NB:
                not_allowed_flights.update(flights_incompatible)
                not_allowed_flights.update(set(filter(lambda flight_index: not aircraft.can_perform_flight(self.flights[flight_index]), flights_compatible)))
            else:
                not_allowed_flights.update(set(filter(lambda flight_index: not aircraft.can_perform_flight(self.flights[flight_index]), [*range(len(self.flights))])))

        not_allowed_flights.update(set(map(lambda flight: flight.flight_index, aircraft.impossible_flights))) # remove impossible flights considering window limits
        if not relaxed:
            not_allowed_flights.update(set(map(lambda flight: flight.flight_index, aircraft.not_recommended_flights)))
        not_allowed_flights.update(aircraft.overlap_flights_indexes) # get set of flights that can not be performed by aircraft
        return not_allowed_flights


    def graph_remove_flights_aircraft(self, aircraft, not_allowed_flights, total_reach, total_not_reach):
        """
        For a given aircraft and structured group of flights (total_reach and total_not_reach) returns the group of flights that are reached and not reached (total_reach_aircraft and total_not_reach_aircraft) removing the flights that are not allowed to be performed by the given aircraft and all the connections that were depending on them 

        Arguments:
            aircraft {Aircraft} -- [description]
            flights_compatible {[type]} -- [description]
            flights_incompatible {[type]} -- [description]
            total_reach {[type]} -- [description]
            total_not_reach {[type]} -- [description]

        Returns:
            [[int]] -- Matrix where for each flight (row) there's a list of indexes of flights that are reached from it(columns)
            [[int]] -- Matrix where for each flight (row) there's a list of indexes of flights that are not reached from it (columns)
        """

       
        # if there's no flights overlapping maintenances nor flights that are not compatible with the aircraft then it's not necessary to do any analysis for the aircraft
        if len(not_allowed_flights) > 0:

            not_reach, vertices = self.flights_graph.get_reach_without_nodes(not_allowed_flights) # get a set to update the the nodes that are not reached after removing the not allowed flights
    
            total_not_reach_aircraft = copy.deepcopy(total_not_reach) # create a temporary copy to not change the original values
            total_reach_aircraft = copy.deepcopy(total_reach)
            for index, vertice in enumerate(vertices):
                try:
                    total_not_reach_aircraft[vertice].update(not_reach[index])
                    if len(total_reach_aircraft[vertice]) > 0:
                        total_reach_aircraft[vertice] -= not_reach[index]
                except:
                    total_not_reach_aircraft[vertice] = not_reach[index]
                    if len(total_reach_aircraft[vertice]) > 0:
                        total_reach_aircraft[vertice] -= not_reach[index]
            
            for to_remove in not_allowed_flights:
                total_not_reach_aircraft[to_remove] = set()
                total_reach_aircraft[to_remove] = set()

            for index, not_reachable in enumerate(total_not_reach_aircraft):
                if (len(total_reach_aircraft[index])) > 0:
                    total_reach_aircraft[index] -= not_allowed_flights
                if len(not_reachable) > 0:
                    total_not_reach_aircraft[index] = not_reachable - not_allowed_flights

        else:
            total_not_reach_aircraft = total_not_reach
            total_reach_aircraft = total_reach

        self.total_not_reach_by_aircraft[aircraft.index] = total_not_reach_aircraft
        return total_reach_aircraft, total_not_reach_aircraft
    
    def get_or_3_variables(self, nodes):
        nodes.sort()
        count_nodes = {node: [] for node in nodes}
        for elem in self.or_aux_variables:
            if len(elem) == 3:
                if elem[0] in count_nodes and elem[1] in count_nodes and elem[2] in count_nodes:
                    count_nodes[elem[0]].append(elem)
                    count_nodes[elem[1]].append(elem)
                    count_nodes[elem[2]].append(elem)
        final_variables = []
        while len(nodes) > 0:
            count_nodes = {k: v for k, v in sorted(count_nodes.items(), key=lambda item: len(item[1]))}
            for count_node in count_nodes:
                if not count_node in nodes:
                    continue
                if len(count_nodes[count_node]) == 0:
                    final_variables.append(count_node)
                    nodes.remove(count_node)
                    break
                other_node = count_nodes[count_node][0]
                final_variables.append(other_node[0]+","+other_node[2]+",or,"+other_node[1])
                for threetuples in count_nodes:
                    for tuple_ in count_nodes[threetuples]:
                        if other_node[0] in tuple_ or other_node[1] in tuple_ or other_node[2] in tuple_:
                            count_nodes[threetuples].remove(tuple_)
                nodes.remove(other_node[0])
                nodes.remove(other_node[1])
                nodes.remove(other_node[2])
        final_variables.sort(key = lambda item: len(item))
        print(final_variables)
        return final_variables


    def get_or_variables(self, initial_nodes):
        nodes = self.get_or_3_variables(initial_nodes)
        count_nodes = {node: [] for node in nodes}
        for pair in self.or_aux_variables:
            if len(pair) == 2:
                if pair[0] in count_nodes and pair[1] in count_nodes:
                    count_nodes[pair[0]].append(pair)
                    count_nodes[pair[1]].append(pair)
        final_variables = []
        while len(nodes) > 0:
            count_nodes = {k: v for k, v in sorted(count_nodes.items(), key=lambda item: len(item[1]))}
            for count_node in count_nodes:
                if not count_node in nodes:
                    continue
                if len(count_nodes[count_node]) == 0:
                    final_variables.append(count_node)
                    nodes.remove(count_node)
                    break
                other_node = count_nodes[count_node][0]
                final_variables.append(other_node[0]+","+other_node[1]+",or")
                for tuples in count_nodes:
                    for tuple_ in tuples:
                        if other_node[0] in tuple_ or other_node[1] in tuple_:
                            count_nodes[tuples].remove(tuple_)
                nodes.remove(count_node)
                nodes.remove(other_node[1])
        final_variables.sort(key = lambda item: len(item))
        return final_variables