# Quantum Tail Assignment

This project aims to create an implementation of the tail assignment problem using a quantum computing approach.

## Authors
Main Author: Luis Noites Martins (luis.noites.martins@fe.up.pt)

Supervisors: Ana Paula Rocha (arocha@fe.up.pt) and António J. M. Castro (frisky.antonio@gmail.com)

## Tail Assignment Problem

The tail assignment problem is the problem of assigning aircraft to flights considering multiple constraints while trying to minimize some objective function.

One important constraint to be considered while solving this problem is the pre-assigned activities each aircraft has, such as maintenance activities.

Multiple implementations were already considered to solve this problem using different algorithms.

In this approach, we will take this problem as a scheduling problem where activities (flights + pre-assigned maintenance) are allocated to aircraft satisfying all the existent constraints.

## Quantum Annealing

Initially, a quantum annealing solution will be created based on the fact that the problem can be considered as a binary constraint problem where each pair aircraft-activity is either 1 (happens) or 0 (doesn't happen)

### Implementation Steps


### Notes

Flights and Maintenances should be previously ordered by Start_Time and End_Time in 2 separate CSV files (flights.csv and maintenances.csv)
Although being considered for the constraints, no maintenances will be found on the resulting bqm as input for the quantum problem. It is not required since these variables are predetermined.

All the maintenances are guaranteed since all the overlap flights are set to 0 and if there's any previous flight to maintenance then it should be on time on the maintenance airport.


Set constraint to ensure that only possible connection between activities that are not possible to perform directly, i.e. activity1.destination != activity2.origin. Since each aircraft can perform different activities due to obligatory maintenances as well as the required model for each flight then for the different aircrafts the following pairs of activities were considered:
1 - Flight-Flight: if 2 flights (A, B) have no direct connection then, if A and B happen, other flight (C) that has a direct connection to B must happen.

2 - Flight-Maintenance/Maintenance-Flight: if a flight (A), has no direct connection to obligatory maintenance (B) then, if A happens, other flight (C) that has a direct connection to B must happen (since B is maintenance and, therefore, will happen)

3 - Maintenance-Maintenance: If 2 obligatory maintenances (A,B) have no direct connection between each other then a path must be ensured between them. Therefore, 2 or more flights must happen (C,D) as A.destination == C.origin and D.destination == B.origin. The connection between C and D is previously ensured due to the connection constraint Flight-Flight.
                    Special scenario: if there's one flight (K) that is able to connect directly A,B (A.destination == K.origin and K.destination == B.origin) then one flight might be enough to ensure this connection). 




Reorder setas and model constraint setting some variables (pair -> flight,aircraft) as 0 as these variables are not valid for the solution of the problem :
1 - if there's a flight associated to an aircraft but this connection is invalid due to the flight required aircraft model then this variable is set to 0 (this should not happened since in previous constraint this is always taken into account and therefore the variable will never be added to the constraint problem)

2 - if the aircraft have not enough seats (in total) for performing the flight then this variable is also set to 0 (this might happen in some scenarios where different aircraft from the same model have a different number of total seats and therefore although the required aircraft model is correct, the number of seats might not be enough to perform some flights)

3 - if the aircraft have not enough business seats considering the business seats sold for a flight then this variable is also set to 0 (similar reason as 2)


PS: Specify that setting the constraint of just assigning one aircraft to each flight have a better performance when it is done while considering the flights that overlap maintenances for each aircraft. It happens because for invalid variables (pair -> flight,aircraft) a constraint is not needed to be added and therefore it allows one to reduce the number of added constraints (that take the majority of the time to calculate the BQM)

Fixed_variables -> some variables are not part of the csp problem as they are obligatory set to 1 to allow the schedule to be valid
Examples:

Maintenance in A
Flight A->B
Maintenance in B
Since there's only one flight that allows both maintenances to be performed then that flight must be assigned to the specific aircraft

If the flight is only possible to be done by one aircraft and it does not overlap any maintenance or does not limit the possibility of allowing all maintenances to happen they it should be fixed to 1

Example of invalid:
Flight: PRT -> LIS
Maintenance: FNC

Although the activities does not overlap if the flight happen then it will not allow the maintenance to happen and therefore the flight can not happen

Extra: Flights that have no connection to the following maintenance or are not reached from the previous maintenance are not added as possible path between 2 maintenances


### QUBO

In order to speedup the model creation this approach aims to create a QUBO directly while setting up the constraints without using any auxiliar library.

Following the same idea as the CSP implementation this approach considers multiple steps, one for each constraint considered:

1. No overlap flights: For each pari of flights that are not possible to be assigned to the same aircraft add an interaction of a positive value (macros.NO_OVERLAP_PARAM)

2. Maximum one aircraft per flight: For each flight that may be operated by more than one aircraft, add an interaction between the variable flight-aircraft1 and flight-aircraft2 of a positive value (macros.MAX_ONE_PARAM)

3. Activity pairs: for each pair of flights that may be operated by the same aircraft and that can not happen since there's no path between the 2 flights, add an interaction between the variable flight1-aircraft and flight2-aircraft of a positive value (macros.NO_PAIR_PARAM)

4 . Possible_connections: for each pair of flights that may be operated by the same aircraft and although having path between them, are not directly connected, the following situation is assumed: if A (initial flight) and B (final flight) are assigned to the same aircraft, then one of the flights that arrive to B and that can be reached from A needs to be assigned to the same aircraft.

 OR( AND(INITIAL, FINAL, INITIAL_FINAL_AND) , (INTERMEDIATE_1 || INTERMEDIATE_2 || INTERMEDIATE_3), OUTPUT)
OUTPUT = 1


Other possible connections are the flights that may happen before maintenances. In that case it is quite similar but this time it is only needed to ensure that if A (initial flight) is assigned to one aircraft that have a maintenance (B), then one of the flights that arrive to B and that can be reached from A needs to be assigned to this aircraft.

OR(XOR(A,1) ,  (INTERMEDIATE_1 || INTERMEDIATE_2 || INTERMEDIATE_3), OUTPUT)
OUTPUT = 1


5 . In order to ensure all the existent maintenances are guaranteed then for each pair of maintenances of the same aircraft that don't take place on the same airport it is necessary to ensure that one of the paths that connect both maintenances happen for the aircraft, i.e, if a maintenance A takes place in LIS and maintenance B takes place in FNC then a flight or a group of flights that allow the aircraft to be on time in both maintenances must be assigned to the considered aircraft. This is done, ensuring that one of the flights that may connect to maintenance A is assigned to the considered aircraft and also one of the flights that may connect to maintenance B is assigned to the same aircraft (no connection between middle flights is needed since it is guaranteed by constraint 3)

(INTERMEDIATE_1 || INTERMEDIATE_2 || INTERMEDIATE_3) -> OUTPUT
OUTPUT = 1

Improvements keep exactly the same from the CSP implementation as they don't depend on the way model is obtained. 


For flights that are already fixed to 1 as being obligatory for an aircraft to perform maintenances, if other flight also requires that flight to ensure its maintenances then a solution is not possible to be obtained. Test -> test_one_flight_to_ensure_maintenances_two_aircraft

### Improved QUBO

In order to reduce the time needed to calculate a QUBo as well as the number of generated variables some adaptions were made to constraints 4 and 5.

For each flight a negative interaction is created between it and each one of the flights that can be performed after it. Doing this, allow to remove the first part of constraint 4 as if each flight is encouraged to be followed by one flight that might connect to it, then the global path is also encouraged and therefore if the used parameters are properly tunned it will ensure all paths between flights are valid

The second condition of constraint 4 is kept as it is necessary to ensure that the chosen paths will guarantee maintenances

Constraint 5 also changed. Instead of obligating paths between maintenances, the flights that may happen before and after each maintenance is encouraged to happen for the proper aircraft and therefore together with the first condition of constraint 4 the paths between maintenances are encouraged


##  Objective Function

Initial Note: Variables with a positive linear coefficient on the bqm are not being considered for the objective function as these variables are most likely to not be chosen for the solution since they may not ensure one of the previous defined constraints (example for when a variable A is depending on other variable B that was already pre fixed to 1 then although A is still part of the constraint problem considering it to the objective function may reuslt in invalid solutions). Plus, when the bqm is determined if the coefficient of a varibale is positive then that variable is more likely to be 0 than one and therefore this coefficent should not be reduced as it may allow the system to consider this varibale as 1 and calculate an invalid solution -> to be analysed

### Minimize Free Seats [Free Seats = Total seats of aircraft - Needed seats for the flight]: 

    To the possible assignments: get the minimum free seats of the possibilities that might interfer with each assignment as baseline, i.e for each pair flight-aircraft find the minimum number of free seats for all the pairs that are composed by either the considered flight or the considered aircraft

    For each possible assignment get the % gap
        gap = ( current_free_seats - min_free_seats ) / current_free_seats	

    For each possible assignment add a bias to improve or worsen the assignment
    (improve → minimize the actual bias)
        bias = -SEATS_PARAM*(1-gap)

    Example: 
        Ex 1: 	Aircraft 1 : Total Seats = 174
	            Aircraft 2: Total Seats = 168

	            Flight 1: Needed Seats = 161

                F1,A1: current_free_seats =  13
                F1,A2: current_free_seats = 7
                min_free_seats = 7

                gap(F1,A1) = 0.4615
                gap(F1,A2) = 0

                bias(F1,A1) = -0.5385
                bias(F1,A2) = -1

        Ex 2: 	Aircraft 1 : Total Seats = 174
	            Aircraft 2: Total Seats = 168

	            Flight 1: Needed Seats = 161
	            Flight 2: Needed Seats = 173

                F1,A1: current_free_seats =  13
                F1,A2: current_free_seats = 7
                F2,A1: current_free_seats = 1
                min_free_seats = 1

                gap(F1,A1) = 0.92307
                gap(F1,A2) = 0.85714
                gap(F2,A1) = 0

                bias(F1,A1) = -0.07693
                bias(F1,A2) = -0.14286
                bias(F2,A1) = -1

    Note: SEATS_PARAM is a positive real-valued number used to tune the relative significance of assigning flights to aircraft


### Minimize Costs [Cost = - Parking (minute_parking_cost*(flight_time+rotation_time)) + Execution (dept_landing_cost + arr_landing_cost + airport_handling + fuel_cost + atc_cost + rotation_parking_cost)]

    To the possible assignments: get the minimum cost of the possibilities that might interfer with each assignment as baseline, i.e for each pair flight-aircraft find the minimum cost for all the pairs that are composed by either the considered flight or the considered aircraft

    For each possible assignment get the % gap
        gap = ( current_cost - min_cost ) / current_cost	

    For each possible assignment add a bias to improve or worsen the assignment
    (improve → minimize the actual bias)
        bias = - COST_PARAM*(1-gap)

    Note 1: COST_PARAM is a positive real-valued number used to tune the relative significance of assigning flights to aircraft
    Note: parking cost is not including time between flights or rotation time and the time is being converted directly from daily cost to minute cost

## Testing

In order to implement tests the unittest package was used.

Tests are defined in the tests folder

For each scheduler type (SchedulerModel and SchedulerFleet) the tests are divided in 3 classes: SimpleTests, ComposedTests and ImprovedTests

In the class SimpleTests are defined the more simple tests for testing the constraint in an individual manner. On the other hand, on the ComposedTests class it is possible to find tests that are more complex and aim to check how the program behaves calculating a solution for a problem that considers multiple constraints. Finally, the ImprovedTests class aims to check how well the defined objective functions work and provide with a good solution rather than just a valid solution

Test command:

    python tests/*

### Code Coverage

In order to analyse the quality and coverage of the code the coverage.py package (https://coverage.readthedocs.io/en/coverage-5.1/) can be used.

Run tests with coverage:
    coverage run --source=src tests/*

After running the tests it is possible to get simplified coverage report:
    coverage report

Or get a nicer presentation in html using:
    coverage html

### Scheduler fleet

It was implemented a scheduler to handle situations where an aircraft model is not pre-assigned to the flights but just a preferential aircraft fleet. For these cases 2 different aircraft fleet are considered:

0. Narrow-Body Aircraft (NB)
1. Wide-Body Aircraft (WB)

Due to the domain context it is considered that a WB can always operate flights that require a NB aircraft but not the other way around, i.e if a flight requires a NB aircraft it can be assigned to a WB aircraft, but if a flight requires a WB aircraft then it can not be assigned to a NB aircraft (even if the NB aircraft has enough seats)

Note: No preference is given for assigning flights to the desired aircraft fleet instead of choosing one from a bigger fleet have higher costs and a considerable bigger number of seats and since these 2 situations are being minimized a flight may just be assigned to a bigger fleet than the required one if there's no other option or this assignment improves the global assignment

### Command line menu

In order to be ale to easily run both scenarios assignment considered a pre-assigned aircraft model or pre-assigned aircraft fleet some adaptions were made for it to be used as a flag --hasAircraftModel which is by default False and when used it is True.

Additionally, an argument was also added to allow the user to set a different path for the folder where the csv data files are saved (--filesDirectory). This path should be given considering as root the root of the project and the names for the files should follow some rules:

* Airports file: airports.csv
* City pairs file: city_pairs.csv
* Aircraft models file: aircraft_models.csv
* Aircraft file: aircraft.csv
* Maintenances file: maintenances.csv
* Flights file with pre-assigned aircraft model: model_flights.csv
* Flights file with pre-assigned aircraft fleet: fleet_flights.csv


Note: Since the SchedulerFleet file was able to handle both situations (flights with pre-assigned model or flights with pre-assigned fleet) it was renamed to Scheduler. The SchedulerModel file was not deleted since it may be interesting to analyse later if for some cases separate files should be used instead of a generic scheduler due to performance issues

<!-- ### Window

For the cases where a window is used the following considerations are taken into account:

While improving the schedule for a specific window it is important to ensure the integrity of the full schedule. Therefore, for the cases where a schedule is previously known, after choosing the window time that will be analysed all the activities that are not totally inside the window (i.e all the activities that don't start and end inside the chosen window time) are fixed. Furthermore, the solution that will be calculated for the given window time will take into account the constraints regarding the possible connection to the window border activities (i.e activities that will happen, for each aircraft, immediately before and after the window time ). It is important to take into account that the window time selection is independent from the beginning or ending of any activity it can happen the case where the window border activities start before the window time but end inside of it or the other way around. These cases are also taken into account -->
