import os, sys
from scheduler.Scheduler import Scheduler
from scheduler.ObjectiveFunction import ObjectiveFunction
import scheduler.QUBO.macros as macros
from models.Activity import Maintenance, Flight
from models.Aircraft import AircraftFleet
import dimod
import dwavebinarycsp
import dwavebinarycsp.factories.constraint.gates as gates
from models.utils.Graph import Graph
import timeit
from collections import defaultdict
import json

def get_label(flight, aircraft):
    return "{flight.flight_index},{aircraft.index}".format(**locals())

def get_aux_label(index1, index2, name, index3 = None):
    if index3 == None:
        return "{index1},{index2},{name}".format(**locals())
    else:
        return "{index1},{index2},{index3},{name}".format(**locals())


class SchedulerQUBO(Scheduler):
    def __init__(self, flights, aircraft, aircraft_models, has_aircraft_model):
        super().__init__(flights, aircraft, aircraft_models, has_aircraft_model)
        self.length_flights = len(self.flights)
        #self.fixed_one_aircraft_variables = set()
        self.fixed_variables = set()
        self.fixed_flights = set()
        self.penalized_pair = []
        self.ands = []
        self.or_aux_var = []
        #self.Q = defaultdict(int)
        self.BQM = dimod.BinaryQuadraticModel(offset=0.0, vartype=dimod.BINARY)

    def add_or_constraint(self, vertices, is_maintenances = False):
        if not is_maintenances:
            macro = macros.PATH_PARAM
        else:
            macro = macros.MAINTENANCES_PARAM

        # B || C || D
        final_vertices = vertices
        prev_vertice = final_vertices[0]
        i=1
        length = len(final_vertices)
        while i < length:
            vertice = final_vertices[i]
            # OR(x,y,z) = x*y+y*z+x*z+2*w-x-y-z-w*x-w*y-w*z
            if i < length-2:
                vertice2 = vertices[i+1]
                next_vertice = get_aux_label(prev_vertice, vertice2, 'or', vertice)
                #self.aux_or_variables.append((prev_vertice, vertice, vertice2))
                #if not next_vertice in self.or_aux_var:
                self.BQM.add_interaction(prev_vertice, vertice, macro)
                #self.Q[prev_vertice, vertice] += macros.PATH_PARAM
                self.BQM.add_interaction(vertice, vertice2, macro)
                #self.Q[vertice, vertice2] += macros.PATH_PARAM
                self.BQM.add_interaction(prev_vertice, vertice2, macro)
                #self.Q[prev_vertice, vertice2] += macros.PATH_PARAM
                self.BQM.add_variable(next_vertice, 2*macro)
                #self.Q[next_vertice, next_vertice] += 2 * macros.PATH_PARAM
                self.BQM.add_variable(prev_vertice, -macro)
                #self.Q[prev_vertice, prev_vertice] += -macros.PATH_PARAM
                self.BQM.add_variable(vertice, -macro)
                #self.Q[vertice, vertice] += -macros.PATH_PARAM
                self.BQM.add_variable(vertice2, -macro)
                #self.Q[vertice2, vertice2] += -macros.PATH_PARAM
                self.BQM.add_interaction(prev_vertice, next_vertice, -macro)
                #self.Q[prev_vertice, next_vertice] += -macros.PATH_PARAM
                self.BQM.add_interaction(vertice, next_vertice, -macro)
                #self.Q[vertice, next_vertice] += -macros.PATH_PARAM
                self.BQM.add_interaction(vertice2, next_vertice, -macro)
                #self.Q[vertice2, next_vertice] += -macros.PATH_PARAM
                    #self.or_aux_var.append(next_vertice)
                i += 2
            # OR(x,y) = x*y-2*x*w-2*y*w+x+y+w    
            else:
                next_vertice = get_aux_label(prev_vertice, vertice, 'or')
                #self.or_aux_variables.append((prev_vertice, vertice))
                #if not next_vertice in self.or_aux_var:
                self.BQM.add_interaction(prev_vertice, vertice, macro)
                #self.Q[prev_vertice, vertice] += macros.PATH_PARAM
                self.BQM.add_interaction(prev_vertice, next_vertice, -2*macro)
                #self.Q[prev_vertice, next_vertice] += -2*macros.PATH_PARAM
                self.BQM.add_interaction(vertice, next_vertice, -2*macro)
                #self.Q[vertice, next_vertice] += -2*macros.PATH_PARAM
                self.BQM.add_variable(prev_vertice, macro)
                #self.Q[prev_vertice, prev_vertice] += macros.PATH_PARAM
                self.BQM.add_variable(vertice, macro)
                #self.Q[vertice, vertice] += macros.PATH_PARAM
                self.BQM.add_variable(next_vertice, macro)
                #self.Q[next_vertice, next_vertice] += macros.PATH_PARAM
                    #self.or_aux_var.append(next_vertice)
                i += 1
            prev_vertice = next_vertice
        return prev_vertice
     
    def add_xor_or_constraint(self, a, b, is_maintenances=False):
        if not is_maintenances:
            macro = macros.PATH_PARAM
        else:
            macro = macros.MAINTENANCES_PARAM
        #OR(XOR(A,1),B) = x*y*(-1)-z+2*x*z-2*y*z-x+2*y ((+1))
        final_vertice = get_aux_label(a, b, 'xor')
        self.BQM.add_interaction(a,b, -macro)
        self.BQM.add_variable(final_vertice, -macro)
        self.BQM.add_interaction(a, final_vertice, 2*macro)
        self.BQM.add_interaction(b, final_vertice, -2*macro)
        self.BQM.add_variable(a, -macro)
        self.BQM.add_variable(b, 2*macro)
        self.BQM.add_offset(1)        
        return final_vertice

    # 3 -> Do not do 2 flights that overlap
    def _add_constraint_no_overlap_flights(self):
        # real_overlaps = set()
        overlap_flights = self.get_flights_connections_and_overlaps() #  overlap_flights
        #flights_incentive_doing = []
        for flight_pair in overlap_flights:
            for aircraft in self.aircraft:
                if aircraft.can_perform_flight(flight_pair[0]) and aircraft.can_perform_flight(flight_pair[1]):
                    act0_index = get_label(flight_pair[0], aircraft)
                    act1_index = get_label(flight_pair[1], aircraft)
                    # if not flight_pair[0] in flights_incentive_doing:
                    #     self.BQM.add_variable(act0_index, -macros.NO_OVERLAP_PARAM)
                    #     flights_incentive_doing.append(flight_pair[0])
                    # if not flight_pair[1] in flights_incentive_doing:
                    #     self.BQM.add_variable(act1_index, -macros.NO_OVERLAP_PARAM)
                    #     flights_incentive_doing.append(flight_pair[1])
                    # real_overlaps.update({flight_pair})
                    self.penalized_pair.append((act0_index, act1_index))
                    self.BQM.add_interaction(act0_index, act1_index, macros.NO_OVERLAP_PARAM)
    
    # 0 -> Each flight should be assigned to maximum one aircraft
    def _add_constraint_maximum_one_aircraft_for_each_flight(self):
        for flight in self.flights:
            aircraft_temp = list(filter(lambda aircraft: aircraft.can_perform_flight(flight), self.aircraft))
            if len(aircraft_temp) >= 1:
                for index, aircraft1 in enumerate(aircraft_temp[:len(aircraft_temp)-1]):
                    aircraft1_index = get_label(flight, aircraft1)
                    self.BQM.add_variable(aircraft1_index, -macros.MAX_ONE_PARAM)
                    self.BQM.add_offset(macros.MAX_ONE_PARAM)
                    for aircraft2 in aircraft_temp[index+1:len(aircraft_temp)]:
                        aircraft2_index = get_label(flight, aircraft2)
                        self.BQM.add_interaction(aircraft1_index, aircraft2_index, 2*macros.MAX_ONE_PARAM)
                aircraft1_index = get_label(flight, aircraft_temp[len(aircraft_temp)-1])
                self.BQM.add_variable(aircraft1_index, -macros.MAX_ONE_PARAM)
                self.BQM.add_offset(macros.MAX_ONE_PARAM)
            # elif len(aircraft_temp) == 1:
            #     label = get_label(flight, aircraft_temp[0])
            #     if not label in list(self.BQM.variables):
            #         try:
            #             self.BQM.fix_variable(label, 1)
            #         except:
            #             pass
            #         self.fixed_one_aircraft_variables.update({label})


    # 1/2 -> if there's no path between 2 activities than they can not be operated by the same aircraft
    # Note: path -> there is no activities that allow being on time in both activities taking into consideration the  for each aircraft
    # TODO -> add restriction that the previous flight of maintenance should end up on the maintenance airport
    def _add_constraint_perform_activity_pair(self):
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
                    if not (flight1_index, flight2_index) in self.penalized_pair and not (flight2_index, flight1_index) in self.penalized_pair:
                        self.BQM.add_interaction(flight1_index, flight2_index, macros.NO_PAIR_PARAM)
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
                    # try:
                    #     self.fixed_one_aircraft_variables.remove(label)
                    # except:
                    #     pass
                    try:
                        self.BQM.fix_variable(label, 0)
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
            prev_vertice = self.add_or_constraint(vertices, True)
            #self.BQM.add_variable(prev_vertice, -macros.CONNECTION_MAINTENANCE_PARAM)
            if len(prev_vertice) == 3:
                self.fixed_flights.update({int(prev_vertice[0])})
            self.fixed_variables.update({prev_vertice})
            self.BQM.fix_variable(prev_vertice, 1)
        elif type_path == 1:
            # XOR(A,1, RES) || (B || C || D)
            initial_vertice = vertices[0]
            intermediate = vertices[1:]
            prev_vertice = self.add_or_constraint(intermediate, True)
            # OR(XOR(x,1),y) = -x*y-z+2*x*z-2*y*z-x+2*y
            # OR(x,y) = x*y-2*x*z-2*y*z+x+y+z
            output = self.add_xor_or_constraint(initial_vertice, prev_vertice, True)
            #self.BQM.add_variable(output, -macros.CONNECTION_MAINTENANCE_PARAM)
            self.fixed_variables.update({output})
            self.BQM.fix_variable(output, 1)
        else:
            # AND(INITIAL, FINAL, INITIAL_FINAL_AND)
            # (INTERMEDIATE_1 || INTERMEDIATE_2 || INTERMEDIATE_3) -> PREV_VERTICE
            # OR(XOR(INITIAL_FINAL_AND, 1), PREV_VERTICE, OUTPUT)
            initial_vertice = vertices[0]
            final_vertice = vertices[1]
            intermediate = vertices[2:]
            # AND(x,y) = x*y - 2*x*z - 2*y*z +3*z
            initial_and = get_aux_label(initial_vertice, final_vertice, 'and')
            #if not initial_and in self.ands:
            self.BQM.add_interaction(initial_vertice, final_vertice, macros.PATH_PARAM)
            #self.Q[initial_vertice, final_vertice] += macros.PATH_PARAM
            self.BQM.add_interaction(initial_vertice, initial_and, -2*macros.PATH_PARAM)
            #self.Q[initial_vertice, initial_and] += -2*macros.PATH_PARAM
            self.BQM.add_interaction(final_vertice, initial_and, -2*macros.PATH_PARAM)
            #self.Q[final_vertice, initial_and] += -2*macros.PATH_PARAM
            self.BQM.add_variable(initial_and, 3*macros.PATH_PARAM)
            #self.Q[initial_and, initial_and] += 3*macros.PATH_PARAM
            #    self.ands.append(initial_and)

            prev_vertice = self.add_or_constraint(intermediate)
            output = self.add_xor_or_constraint(initial_and, prev_vertice)
            self.fixed_variables.update({output})
            self.BQM.fix_variable(output, 1)

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
                    # try:
                    #     self.fixed_one_aircraft_variables.remove(label)
                    # except:
                    #     pass
                    try:
                        self.BQM.fix_variable(label, 0)
                    except:
                        pass


    def get_bqm(self, export_bqm_path=None, stitch_kwargs=None):

        if stitch_kwargs is None:
            stitch_kwargs = {}
        
        initialtime = timeit.default_timer()
        
        # TODO -> check if should be in scheduler constructor
        self.pre_analysis_and_constraints()

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

        #e_offset = (macros.MAX_ONE_PARAM * len(self.aircraft)) + (macros.HARD_NO_PAIR * len(self.flights)) + (macros.PATH_PARAM * len(self.flights))
        #bqm = BinaryQuadraticModel.from_qubo(self.Q, offset=e_offset)
        variables = set(self.BQM.variables)
        initial_fixed = self.fixed_variables.difference(variables)
        #aircraft_fixed = self.fixed_one_aircraft_variables.difference(variables)
        fixed_variables = list(initial_fixed)

        self.BQM.normalize([-1, 1], [-2,2])

        #print("Maximum element is {:.2f} and minimum is {:.2f}.".format(max(max(self.BQM.linear.values()), max(self.BQM.quadratic.values())), min((min(self.BQM.linear.values()), min(self.BQM.quadratic.values())))))

        objective_function = ObjectiveFunction(self.aircraft, self.flights, self.overlap_flights, self.total_not_reach_by_aircraft)
        bqm = objective_function.improve_combined_params(self.BQM, macros.OBJECTIVE_PARAM)
        finaltime = timeit.default_timer() - initialtime
        if not export_bqm_path is None:
            with open(export_bqm_path+'/QUBO_BQM.json', 'w') as outfile:
                json_data = self.BQM.to_serializable()
                json_data['modeling'] = "QUBO"
                json_data["fixed_variables"] = fixed_variables
                json_data["modeling_time"] = finaltime
                json.dump(json_data, outfile)
            outfile.close()
            print("QUBO BQM exported as QUBO_BQM.json")
        # bqm = objective_function.improve_bqm_min_free_seats(self.BQM, macros.SEATS_PARAM)
        # bqm = objective_function.improve_bqm_min_costs(self.BQM, macros.COST_PARAM)

        return self.BQM, fixed_variables, finaltime

    ############## --------------------------------------------- TODO ------------------------------------------ ##############
    

    def __get_activities_graph(self):
        temp_edges = [0]* len(self.activities)
        activities_graph = Graph(len(self.activities)) # graph of flights and connections between them
        for activity1 in self.activities[:len(self.activities)-1]:
            for activity2 in self.activities[activity1.activity_index+1:]:
                if activity1.compatible_activity(activity2) and not activity1.check_overlap(activity2):
                        if activity1.destination == activity2.origin:
                                activities_graph.add_edge(activity1.activity_index, activity2.activity_index)  # add edge between flghts that can be consecutive
                                temp_edges[activity1.activity_index] += 1
                                temp_edges[activity2.activity_index] += 1

        for index, i in enumerate(temp_edges):  # add nodes that have no connection to graph to be considered for the not reachable sets
            if i == 0:
                activities_graph.add_edge(index, index)
        return activities_graph        
    
    def __process_data(self):
        acitivites_graph = self.__get_activities_graph() # get initial graph
        groupable = acitivites_graph.get_groupable_vertices()
        for index, elem in enumerate(groupable):
            if len(elem) > 0:
                if isinstance(self.activities[index], Maintenance):
                    print("Maintenance: ", index, ":", elem)
                else:
                    print("Flight: ", index, ":", elem)



    
    #def _edit_bqm_for_lowest_cost(self):


    