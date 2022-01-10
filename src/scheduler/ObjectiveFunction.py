class ObjectiveFunction:
    def __init__(self, aircraft, flights, overlap_flights, no_reach_pair_by_aircraft):
        self.aircraft = aircraft
        self.flights = flights
        self.overlap_flights = overlap_flights
        self.no_reach_pair_by_aircraft = no_reach_pair_by_aircraft #[[[not_pair_flight1, not_pair_flight2]],[]] #aircraft_index[flight_index[other_flight_index]]
    
    def group_bqm_var(self, bqm):
        bqm_variables = list(bqm.variables)
        flights_aircraft = [[] for i in range(len(self.flights))]
        aircraft_flights = [[] for i in range(len(self.aircraft))]
        for index, var in enumerate(bqm_variables):
            if bqm.linear[var] > 0:
                continue
            elems = var.split(',')
            if len(elems) == 2: # [flight_index, aircraft_index]
                flight_index = int(elems[0])
                aircraft_index = int(elems[1])
                flights_aircraft[flight_index].append(aircraft_index)
                aircraft_flights[aircraft_index].append(flight_index)
        return flights_aircraft, aircraft_flights
        
    def calculate_max_matrix(self, flights_aircraft, aircraft_flights, seats):
        print(flights_aircraft)
        print(aircraft_flights)
        matrix_maximum = [[0 for j in range(len(self.flights))] for i in range(len(self.aircraft))]
        matrix= [[-1 for j in range(len(self.flights))] for i in range(len(self.aircraft))]
        for flight_index, aircraft_indexes in enumerate(flights_aircraft):
            maximum_value = 0
            flight = self.flights[flight_index]
            for aircraft_index in aircraft_indexes:
                aircraft = self.aircraft[aircraft_index]
                
                if seats is True:
                    value = aircraft.total_seats - flight.needed_seats
                else:
                    value = flight.get_cost(aircraft)
                matrix[aircraft_index][flight_index] = value
                
                if value > maximum_value:
                    maximum_value = value
            
            for aircraft_index in range(len(self.aircraft)):
                if aircraft_index in aircraft_indexes:
                    matrix_maximum[aircraft_index][flight_index] = maximum_value

        # for aircraft_index, flights_indexes in enumerate(aircraft_flights):
        #     aircraft = self.aircraft[aircraft_index]
        #     for flight_index in flights_indexes:
                
        #         maximum_value = matrix[aircraft_index][flight_index]
                
        #         unperformable_flights_together_flight_index = self.calculate_unperformable_flights(flight_index, aircraft_index)

        #         for unperformable_flight_index in unperformable_flights_together_flight_index:
        #             if unperformable_flight_index in flights_indexes:
        #                 flight = self.flights[unperformable_flight_index] 
        #                 if seats is True:
        #                     value = aircraft.total_seats - flight.needed_seats
        #                 else:
        #                     value = flight.get_cost(aircraft)
        #                     print(value)
        #                 if value > maximum_value:
        #                     maximum_value = value

        #         if maximum_value > matrix_maximum[aircraft_index][flight_index]:
        #             matrix_maximum[aircraft_index][flight_index] = maximum_value

        return matrix_maximum, matrix
    
    def calculate_min_matrix(self, flights_aircraft, aircraft_flights, seats):
        matrix_minimum = [[float('inf') for j in range(len(self.flights))] for i in range(len(self.aircraft))]
        matrix= [[float('inf') for j in range(len(self.flights))] for i in range(len(self.aircraft))]
        for flight_index, aircraft_indexes in enumerate(flights_aircraft):
            minimum_value = float('inf')
            flight = self.flights[flight_index]
            for aircraft_index in aircraft_indexes:
                aircraft = self.aircraft[aircraft_index]
                
                if seats is True:
                    value = aircraft.total_seats - flight.needed_seats
                else:
                    value = flight.get_cost(aircraft)
                matrix[aircraft_index][flight_index] = value
                
                if value < minimum_value:
                    minimum_value = value
            
            for aircraft_index in range(len(self.aircraft)):
                if aircraft_index in aircraft_indexes:
                    matrix_minimum[aircraft_index][flight_index] = minimum_value

        # for aircraft_index, flights_indexes in enumerate(aircraft_flights):
        #     aircraft = self.aircraft[aircraft_index]
        #     for flight_index in flights_indexes:
                
        #         minimum_value = matrix[aircraft_index][flight_index]
                
        #         unperformable_flights_together_flight_index = self.calculate_unperformable_flights(flight_index, aircraft_index)

        #         for unperformable_flight_index in unperformable_flights_together_flight_index:
        #             if unperformable_flight_index in flights_indexes:
        #                 flight = self.flights[unperformable_flight_index] 
        #                 if seats is True:
        #                     value = aircraft.total_seats - flight.needed_seats
        #                 else:
        #                     value = flight.get_cost(aircraft)
        #                 if value < minimum_value:
        #                     minimum_value = value

        #         if minimum_value < matrix_minimum[aircraft_index][flight_index]:
        #             matrix_minimum[aircraft_index][flight_index] = minimum_value

        return matrix_minimum, matrix
    
    def calculate_unperformable_flights(self, flight_index, aircraft_index):
        unperformable = set()
        for overlap_pair in self.overlap_flights:
            print(overlap_pair)
            if overlap_pair[0].flight_index == flight_index:
                unperformable.update({overlap_pair[1].flight_index})
            elif overlap_pair[1].flight_index == flight_index:
                unperformable.update({overlap_pair[0].flight_index})

        not_reached_matrix = self.no_reach_pair_by_aircraft[aircraft_index]
        print(not_reached_matrix)
        for i in range(flight_index):
            if flight_index in not_reached_matrix[i]:
                unperformable.update({i})
        unperformable.update(set(not_reached_matrix[flight_index]))
        return unperformable
            
    def improve_bqm_min_free_seats(self, bqm, param=1, csp=False):
        flights_aircraft, aircraft_flights = self.group_bqm_var(bqm)
        if not csp:
            matrix_baseline, matrix = self.calculate_max_matrix(flights_aircraft, aircraft_flights, True)
        else:
            matrix_baseline, matrix = self.calculate_min_matrix(flights_aircraft, aircraft_flights, True)
        for aircraft_index, aircraft_flights in enumerate(matrix):
            for flight_index, free_seats in enumerate(aircraft_flights):
                if free_seats == -1 or free_seats == float('inf'):
                    continue
                if free_seats == 0:
                    gap = 0
                else:
                    if not csp:
                        gap = free_seats/matrix_baseline[aircraft_index][flight_index]
                    else:
                        gap = matrix_baseline[aircraft_index][flight_index]/free_seats
                if not csp and free_seats > matrix_baseline[aircraft_index][flight_index]:
                    raise ValueError("Error while minimizing free seats")
                if not csp:
                    bias = param*gap
                else:
                    bias = -param*gap
                print(flight_index,",", aircraft_index, ": ", bias)
                bqm.add_variable("{flight_index},{aircraft_index}".format(flight_index = flight_index, aircraft_index = aircraft_index), bias)
        return bqm
    
    def improve_bqm_min_costs(self, bqm, param=1, csp=False):
        flights_aircraft, aircraft_flights = self.group_bqm_var(bqm)
        if not csp:
            matrix_baseline, matrix = self.calculate_max_matrix(flights_aircraft, aircraft_flights, False)
        else:
            matrix_baseline, matrix = self.calculate_min_matrix(flights_aircraft, aircraft_flights, False)
        for aircraft_index, aircraft_flights in enumerate(matrix):
            for flight_index, cost in enumerate(aircraft_flights):
                if cost == float('inf') or cost == -1:
                    continue
                if cost == 0:
                    gap = 0
                else:
                    if not csp:
                        gap = cost/matrix_baseline[aircraft_index][flight_index]
                    else:
                        gap = matrix_baseline[aircraft_index][flight_index]/cost
                    
                if not csp and cost > matrix_baseline[aircraft_index][flight_index]:
                    raise ValueError("Error while minimizing free seats")
                
                if not csp:
                    bias = param*gap
                    print("BIAS: ",bias, " GAP: ", gap)
                else:
                    bias = -param*gap
                print(flight_index,",", aircraft_index, ": ", bias)
                bqm.add_variable("{flight_index},{aircraft_index}".format(flight_index = flight_index, aircraft_index = aircraft_index), bias)
        return bqm

    def improve_combined_params(self, bqm, param, csp=False):
        if csp:
            bqm = self.improve_bqm_min_costs(bqm, param, csp)
        else:
            print(len(list(bqm.variables)))
            bqm = self.improve_bqm_min_costs(bqm, param)
        return bqm

    # def improve_bqm_min_free_seats(self, bqm, param):
    #     bqm_variables = list(bqm.variables)
    #     seats = {}
    #     flights_minimum = {}
    #     aircraft_minimum = {}
    #     for index, var in enumerate(bqm_variables):
    #         if bqm.linear[var] > 0:
    #             continue
    #         elems = var.split(',')
    #         if len(elems) == 2: # [flight_index, aircraft_index]
    #             flight_index = int(elems[0])
    #             aircraft_index = int(elems[1])
    #             flight = self.flights[flight_index]
    #             aircraft = self.aircraft[aircraft_index]
    #             free_seats = aircraft.total_seats - flight.needed_seats
    #             seats.update({(flight_index, aircraft_index, index): free_seats})
    #             if flight.flight_index in flights_minimum:
    #                 if free_seats < flights_minimum[flight.flight_index]:
    #                     flights_minimum[flight.flight_index] = free_seats
    #             else:
    #                 flights_minimum.update({flight.flight_index: free_seats})
    #             if aircraft.index in aircraft_minimum:
    #                 if free_seats < aircraft_minimum[aircraft.index]:
    #                     aircraft_minimum[aircraft.index] = free_seats
    #             else:
    #                 aircraft_minimum.update({aircraft.index: free_seats})
    #     for seats_flight in seats:
    #         if seats[seats_flight] == 0:
    #             gap = 0
    #         else:
    #             minimum_free_seats = min(flights_minimum[seats_flight[0]], aircraft_minimum[seats_flight[1]])
    #             gap = (seats[seats_flight]-minimum_free_seats)/seats[seats_flight] # free seats should be always >= flights.min_free_seats
    #         if seats[seats_flight] < minimum_free_seats:
    #             print("RIIIIPPP")
    #         bias = -param*(1-gap)
    #         bqm.add_variable(bqm_variables[seats_flight[2]], bias)
    #     return bqm


    # def improve_bqm_min_costs(self, bqm, param):
    #     bqm_variables = list(bqm.variables)
    #     costs = {}
    #     flights_minimum = {}
    #     aircraft_minimum = {}
    #     for index, var in enumerate(bqm_variables):
    #         if bqm.linear[var] >  0:
    #             continue
    #         elems = var.split(',')
    #         if len(elems) == 2: # [flight_index, aircraft_index]
    #             flight_index = int(elems[0])
    #             aircraft_index = int(elems[1])
    #             flight = self.flights[flight_index]
    #             aircraft = self.aircraft[aircraft_index]
    #             cost = flight.get_cost(aircraft)
    #             costs.update({(flight_index, aircraft_index, index): cost})
    #             if flight.flight_index in flights_minimum:
    #                 if cost < flights_minimum[flight.flight_index]:
    #                     flights_minimum[flight.flight_index] = cost
    #             else:
    #                 flights_minimum.update({flight.flight_index: cost})
    #             if aircraft.index in aircraft_minimum:
    #                 if cost < aircraft_minimum[aircraft.index]:
    #                     aircraft_minimum[aircraft.index] = cost
    #             else:
    #                 aircraft_minimum.update({aircraft.index: cost})
    #     for cost in costs:
    #         if costs[cost] == 0:
    #             gap = 0
    #         else:
    #             minimum_cost = min(flights_minimum[cost[0]], aircraft_minimum[cost[1]])
    #             gap = float((costs[cost] - minimum_cost)/costs[cost])
    #         if costs[cost] < minimum_cost:
    #             print("RIPPPP")
    #         bias = -param*(1-gap)
    #         bqm.add_variable(bqm_variables[cost[2]], bias)
    #     return bqm