import os, sys
from scheduler.Scheduler import Scheduler
import scheduler.CSP.macros as macros
from models.Activity import Maintenance, Flight
from models.Aircraft import AircraftFleet
from scheduler.ObjectiveFunction import ObjectiveFunction
import dwavebinarycsp
import dwavebinarycsp.factories.constraint.gates as gates
from models.utils.Graph import Graph
import timeit
import json

def get_label(flight, aircraft):
    """Creates a standardized name for variables in the constraint satisfaction problem,
    Scheduler.csp.
    """
    a = "{flight.flight_index},{aircraft.index}".format(**locals())
    return a

def get_aux_label(v0, v1, name):

    return "{v0},{v1},{name}".format(**locals())


class SchedulerCSP(Scheduler):
    def __init__(self, flights, aircraft, aircraft_models, has_aircraft_model):
        super().__init__(flights, aircraft, aircraft_models, has_aircraft_model)
        self.fixed_one_aircraft_variables = set()
        self.fixed_variables = set()
        self.fixed_flights = set()
        self.csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)

    # 3 -> Do not do 2 flights that overlap
    def _add_constraint_no_overlap_flights(self):
        # real_overlaps = set()
        valid_edges = {(0, 0), (1, 0), (0, 1)}
        overlap_flights = self.get_flights_connections_and_overlaps()
        for flight_pair in overlap_flights:
            for aircraft in self.aircraft:
                if aircraft.can_perform_flight(flight_pair[0]) and aircraft.can_perform_flight(flight_pair[1]):
                    # real_overlaps.update({flight_pair})
                    self.csp.add_constraint(valid_edges, {get_label(flight_pair[0], aircraft), get_label(flight_pair[1], aircraft)})
    
    # 0 -> Each flight should be assigned to maximum one aircraft
    def _add_constraint_maximum_one_aircraft_for_each_flight(self):
        valid_edges = {(0, 0), (1, 0), (0, 1)}
        for flight in self.flights:
            aircraft_temp = list(filter(lambda aircraft: aircraft.can_perform_flight(flight), self.aircraft))
            if len(aircraft_temp) > 1:
                for index, aircraft1 in enumerate(aircraft_temp[:len(aircraft_temp)-1]):
                    for aircraft2 in aircraft_temp[index+1:len(aircraft_temp)]:
                        self.csp.add_constraint(valid_edges, {get_label(flight, aircraft1), get_label(flight, aircraft2)})
            elif len(aircraft_temp) == 1:
                label = get_label(flight, aircraft_temp[0])
                if not label in list(self.csp.variables):
                    try:
                        self.csp.fix_variable(label, 1)
                    except:
                        pass
                    self.fixed_one_aircraft_variables.update({label})


    # 1/2 -> if there's no path between 2 activities than they can not be operated by the same aircraft
    # Note: path -> there is no activities that allow being on time in both activities taking into consideration the maintenances for each aircraft
    # TODO -> add restriction that the previous flight of maintenance should end up on the maintenance airport
    def _add_constraint_perform_activity_pair(self):
        valid_edges = {(0, 0), (1, 0), (0, 1)}
        total_reach, total_not_reach = self.flights_graph.get_all() # get list of reachable and not reachable nodes for all flights
        
        flights_compatible, flights_incompatible = self.get_aircraft_flights_compatibility()
  
        for aircraft in self.aircraft:

            not_allowed_flights = self.get_not_allowed_flights_by_aircraft(aircraft, flights_compatible, flights_incompatible)

            total_reach_aircraft, total_not_reach_aircraft = self.graph_remove_flights_aircraft(aircraft, not_allowed_flights, total_reach, total_not_reach)
            
            # add no connection constraints
            #print("AIRCRAFT: ", aircraft.index, ": ", total_not_reach_aircraft)
            for index, not_reachable_nodes in enumerate(total_not_reach_aircraft):
                for not_reachable_node in not_reachable_nodes:
                    flight1_index = get_label(self.flights[index], aircraft)
                    flight2_index = get_label(self.flights[not_reachable_node], aircraft)
                    self.csp.add_constraint(valid_edges, {flight1_index, flight2_index})
            self._add_constraint_possible_connection(aircraft, total_reach_aircraft)


    def _add_constraint_possible_connection(self, aircraft, reach):

        for vertice, set_reach in enumerate(reach): #iterate over the vertices (initial vertice for each iteration)
            for other_vertice in set_reach:         # iterate over the vertices reached by the initial vertice (final vertice for each iteration)
                adj = self.flights_graph.get_adj(vertice) # vertices that are directly connected to the initial vertice
                if not other_vertice in adj: #if there's direct connection between initial and final vertices no need to add constraint since they can happen independently
                    vertice_that_allow_connection = self.flights_graph.get_arrive_to(other_vertice) # vertices that arrive to the final vertice
                    intermediate_vertices = [get_label(self.flights[vertice], aircraft), get_label(self.flights[other_vertice], aircraft)]
                    for connection_vertice in vertice_that_allow_connection:
                        if connection_vertice in set_reach:
                            intermediate_vertices.append(get_label(self.flights[connection_vertice], aircraft))
                    # TODO -> add constraint one of the members list[2:] must be one if initial and final are both one (has initial and final included)
                    self._add_constraint_make_path(intermediate_vertices, 2) 

        if len(aircraft.maintenances) > 0:
            maintenance_index = 0
            next_maintenance = aircraft.maintenances[maintenance_index]
            prev_maintenance = None
            invalid_maintenances_flights = set()
            for vertice, set_reach in enumerate(reach):
                connection_is_possible = True
                flight = self.flights[vertice]
                if not aircraft.can_perform_flight(flight):
                    continue
                
                if not (next_maintenance is None):
                    while flight.original_activity_index > next_maintenance.original_activity_index:
                        prev_maintenance = next_maintenance
                        if maintenance_index < len(aircraft.maintenances) -1:
                            maintenance_index += 1
                            next_maintenance = aircraft.maintenances[maintenance_index]
                        else:
                            next_maintenance = None
                            break 
                if not (next_maintenance is None):  #has next maintenance so flights before the next maintenance are being analysed
                    if flight.destination != next_maintenance.origin:
                        flights = set_reach.intersection(set(map(lambda prev_flight: prev_flight.flight_index, next_maintenance.prev_flights)))
                        if len(flights) > 0:
                            connection_vertices = [get_label(self.flights[vertice], aircraft)]
                            for connection_flight in flights:
                                connection_vertices.append(get_label(self.flights[connection_flight], aircraft))
                            self._add_constraint_make_path(connection_vertices, 1)
                        else:
                            connection_is_possible = False

                if not (prev_maintenance is None) and connection_is_possible == True:  # has prev maintenance so flights after the prev maintenance are being analysed. If it is a flight between maintenances and has no possible conneciton to the next maintenance it is not necessary to analyse as it is an invalid choice
                    if prev_maintenance.destination != flight.origin:
                        flights = []
                        for next_flight in prev_maintenance.pos_flights:
                            if vertice in reach[next_flight.flight_index]:
                                flights.append(get_label(self.flights[next_flight.flight_index], aircraft))
                        if len(flights) > 0:
                            connection_vertices = [get_label(self.flights[vertice], aircraft)]+flights
                            self._add_constraint_make_path(connection_vertices, 1)
                        else:
                            connection_is_possible = False
                        # TODO -> connection between prev maintenance and flight

                #For flights that are not able to connect to maintenances set them to 0 or remove them from the fixed_variables list if they exist there
                if connection_is_possible == False:
                    label = get_label(flight, aircraft)
                    invalid_maintenances_flights.update({flight.flight_index})
                    try:
                        self.fixed_variables.remove(label)
                        self.fixed_flights.remove(flight.flight_index)
                    except:
                        pass
                    try:
                        self.fixed_one_aircraft_variables.remove(label)
                    except:
                        pass
                    try:
                        self.csp.fix_variable(label, 0)
                    except:
                        pass
            for index, maintenance in enumerate(aircraft.maintenances):         #iterate over maintenances to ensure that flights that connect maintenances must happen
                if index > 0 and maintenance.origin != aircraft.maintenances[index-1].destination:
                    prev_maintenance_between = aircraft.maintenances[index-1]
                    prev_connection_flights = set(map(lambda prev_flight: prev_flight.flight_index, maintenance.prev_flights))
                    prev_connection_flights -= aircraft.overlap_flights_indexes
                    prev_connection_flights -= invalid_maintenances_flights
                    prev_connection_flights -= self.fixed_flights
                    if len(prev_connection_flights) > 0:
                        prev_connection_flights_label = list(map(lambda x: get_label(self.flights[x], aircraft), prev_connection_flights))
                        self._add_constraint_make_path(prev_connection_flights_label, 0)
                    else:
                        intersect = prev_connection_flights.intersection(self.fixed_flights)
                        if len(intersect) > 0:
                            for fixed_var in self.fixed_variables:
                                if len(fixed_var) == 3 and int(fixed_var[0]) == intersect and int(fixed_var[3]) != aircraft.index:
                                    #print("Maintenances for aircraft: ", str(aircraft.index), " will require extra flight")
                                    raise NameError("Impossible getting a schedule considering maintenances for aircraft: "+str(aircraft.index), " maintenances: ", maintenance.short_repr(), " and ", prev_maintenance_between.short_repr())
                        else:
                            raise NameError("Impossible getting a schedule considering maintenances for aircraft: "+str(aircraft.index), " maintenances: ", maintenance.short_repr(), " and ", prev_maintenance_between.short_repr())

                    pos_connection_flights = set(map(lambda flight: flight.flight_index, prev_maintenance_between.pos_flights))
                    pos_connection_flights -= aircraft.overlap_flights_indexes
                    pos_connection_flights -= invalid_maintenances_flights
                    pos_connection_flights -= self.fixed_flights
                    if prev_connection_flights == pos_connection_flights:
                        continue
                    if len(pos_connection_flights) > 0:
                        pos_connection_flights_label = list(map(lambda x: get_label(self.flights[x], aircraft), pos_connection_flights))
                        self._add_constraint_make_path(pos_connection_flights_label, 0)
                    else:
                        intersect = prev_connection_flights.intersection(self.fixed_flights)
                        if len(intersect) > 0:
                            for fixed_var in self.fixed_variables:
                                if len(fixed_var) == 3 and int(fixed_var[0]) == intersect and int(fixed_var[3]) != aircraft.index:
                                    #print("Maintenances for aircraft: ", str(aircraft.index), " will require extra flight")
                                    raise NameError("Impossible getting a schedule considering maintenances for aircraft: "+str(aircraft.index), " maintenances: ", maintenance.short_repr(), " and ", prev_maintenance_between.short_repr())
                        else:
                            raise NameError("Impossible getting a schedule considering maintenances for aircraft: "+str(aircraft.index), " maintenances: ", maintenance.short_repr(), " and ", prev_maintenance_between.short_repr())

    

    def _add_constraint_make_path(self, vertices, type_path):
        if type_path == 0:
            # B || C || D
            prev_var = vertices[0]
            i = 1
            while i<len(vertices):
                vertice = vertices[i]
                next_var = get_aux_label(prev_var, vertice, 'or')
                self.csp.add_constraint(gates.or_gate([prev_var, vertice, next_var]))
                prev_var = next_var
                i += 1
            if len(prev_var) == 3:
                self.fixed_flights.update({int(prev_var[0])})
            self.csp.fix_variable(prev_var, 1)
            self.fixed_variables.update({prev_var})
        elif type_path == 1:
            # XOR(A,1, RES) || (B || C || D)
            initial = vertices[0]
            intermediate = vertices[1:]
            prev_var = intermediate[0]
            i = 1
            while i<len(intermediate):
                vertice = intermediate[i]
                next_var = get_aux_label(prev_var, vertice, 'or')
                self.csp.add_constraint(gates.or_gate([prev_var, vertice, next_var]))
                prev_var = next_var
                i += 1
            self.csp.add_constraint({(0,0),(0,1),(1,1)}, [initial, prev_var])
        else:
            # AND(INITIAL, FINAL, INITIAL_FINAL_AND)
            # XOR(INITIAL_FINAL_AND, EXT_1, INITIAL_FINAL_AND_EXT_1_XOR)
            # (INTERMEDIATE_1 || INTERMEDIATE_2 || INTERMEDIATE_3)
            # OR(INITIAL_FINAL_AND_EXT_1_XOR, )
            initial = vertices[0]
            final = vertices[1]
            intermediate = vertices[2:]
            initial_and = get_aux_label(initial, final, 'and')
            self.csp.add_constraint(gates.and_gate([initial, final, initial_and]))
            prev_var = intermediate[0]
            i = 1
            while i<len(intermediate):
                vertice = intermediate[i]
                next_var = get_aux_label(prev_var, vertice, 'or')
                self.csp.add_constraint(gates.or_gate([prev_var, vertice, next_var]))
                prev_var = next_var
                i += 1
            self.csp.add_constraint({(0,0),(0,1),(1,1)}, [initial_and, prev_var])

    #4 -> set 0 to all flights that overlap maintenances,
    #5/6 -> regulamentary laws and ensure the usage of the proper model
    def _add_constraint_no_unperformable_flights(self):
        for flight in self.flights:
            for aircraft in self.aircraft:
                if not aircraft.can_perform_flight(flight):
                    label = get_label(flight, aircraft)
                    try:
                        self.fixed_variables.remove(label)
                    except:
                        pass
                    try:
                        self.fixed_one_aircraft_variables.remove(label)
                    except:
                        pass
                    try:
                        self.csp.fix_variable(label, 0)
                    except:
                        pass


    def get_bqm(self, export_bqm_path=None, stitch_kwargs=None):

        if stitch_kwargs is None:
            stitch_kwargs = {}

        initialtime = timeit.default_timer()

        self.pre_analysis_and_constraints()
        
        # self._process_data()
        starttime = timeit.default_timer()
        self._add_constraint_no_overlap_flights() #3 -> do not do 2 flights that overlap
        print("NO OVERLAP FLIGHTS DONE IN: ", timeit.default_timer() - starttime)
        starttime = timeit.default_timer()
        self._add_constraint_maximum_one_aircraft_for_each_flight() #0 -> all flights should be assigned to not more than one aircraft
        print("MAX ONE AIRCRAFT DONE IN: ", timeit.default_timer() - starttime)
        starttime = timeit.default_timer()
        self._add_constraint_perform_activity_pair() #1/2 -> be in the departure airport on time; be on the maintenance aiport on time
        print("PERFORMABLE PAIRS DONE IN: ", timeit.default_timer() - starttime)
        starttime = timeit.default_timer()
        #self._add_constraint_no_unperformable_flights() #4 -> set 0 to all flights that overlap maintenances, #5/6 -> regulamentary laws and ensure the usage of the proper model
        print("REMOVE UNPERFORMABLE FLIGHTS DONE IN: ", timeit.default_timer() - starttime)

        bqm = dwavebinarycsp.stitch(self.csp, **stitch_kwargs)

        variables = set(bqm.variables)
        initial_fixed = self.fixed_variables.difference(variables)
        aircraft_fixed = self.fixed_one_aircraft_variables.difference(variables)
        fixed_variables = list(initial_fixed|aircraft_fixed)

        # for var in variables:
        #     bqm.add_variable(var, -1)

        bqm.normalize([-1, 1], [-2,2])

        objective_function = ObjectiveFunction(self.aircraft, self.flights, self.overlap_flights, self.total_not_reach_by_aircraft)
        bqm = objective_function.improve_combined_params(bqm, macros.OBJECTIVE_PARAM, True)
        finaltime = timeit.default_timer() - initialtime
        #bqm = objective_function.improve_bqm_min_costs(bqm, macros.COST_PARAM)

        if not export_bqm_path is None:
            with open(export_bqm_path+'/CSP_BQM.json', 'w') as outfile:
                json_data = bqm.to_serializable() 
                json_data['modeling'] = "CSP"
                json_data["fixed_variables"] = fixed_variables
                json_data["modeling_time"] = finaltime
                json.dump(json_data, outfile)
            outfile.close()
            print("CSP BQM exported as CSP_BQM.json")
        return bqm, fixed_variables, finaltime


    