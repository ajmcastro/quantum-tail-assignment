# Quantum Tail Assignment

[![Python](https://img.shields.io/badge/Python-3-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![D-Wave](https://img.shields.io/badge/D--Wave-Quantum%20Annealing-008CD7.svg)](https://www.dwavesys.com/)
[![Ocean SDK](https://img.shields.io/badge/Ocean%20SDK-Quantum%20Optimization-008CD7.svg)](https://docs.dwavequantum.com/)
[![QUBO](https://img.shields.io/badge/QUBO-Combinatorial%20Optimization-6A5ACD.svg)](https://docs.dwavequantum.com/en/latest/concepts/models.html)
[![Quantum Annealing](https://img.shields.io/badge/Quantum%20Annealing-Optimization-663399.svg)](https://www.dwavesys.com/solutions-and-products/quantum-computing/)
[![Aviation](https://img.shields.io/badge/Aviation-Tail%20Assignment-1E90FF.svg)](https://en.wikipedia.org/wiki/Tail_assignment)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

**Quantum and hybrid optimization approaches for the airline Tail Assignment Problem using QUBO formulations and the D-Wave quantum annealing ecosystem.**

The **Tail Assignment Problem (TAP)** determines which individual aircraft should operate each flight while satisfying operational constraints such as aircraft compatibility, passenger capacity, maintenance requirements, temporal feasibility, and aircraft routing.

This project investigates how TAP can be represented as a **Binary Quadratic Model (BQM)** and, in particular, as a **Quadratic Unconstrained Binary Optimization (QUBO)** problem. The resulting formulation can be solved using quantum annealing, quantum-classical hybrid methods, and classical BQM solvers available through the D-Wave ecosystem.

The repository was developed as a research project at the intersection of **airline operations research**, **combinatorial optimization**, and **quantum computing**.

---

## Overview

Tail assignment is an important aircraft scheduling problem in airline operations.

Given:

- a set of flights,
- a fleet of individual aircraft,
- aircraft models or aircraft fleets,
- passenger demand,
- airport information,
- maintenance activities,
- operational costs,

the goal is to construct a feasible assignment of aircraft to flights while optimizing the quality and operational cost of that assignment.

A possible aircraft-flight assignment is represented by a binary decision variable:

```text
x(f, a) = 1   if aircraft a operates flight f
x(f, a) = 0   otherwise
```

The assignment problem can therefore be mapped naturally to a binary optimization problem.

Conceptually, the workflow implemented by the project is:

```text
Airline operational data
        │
        ▼
Feasibility preprocessing
        │
        ▼
Tail-assignment constraints
        │
        ├── Aircraft compatibility
        ├── Seat capacity
        ├── Flight overlap
        ├── Aircraft continuity
        └── Maintenance feasibility
        │
        ▼
   CSP or direct QUBO
        │
        ▼
Binary Quadratic Model
        │
        ├── Quantum annealing
        ├── Quantum-classical hybrid
        ├── Simulated annealing
        ├── Tabu search
        └── Exact solving
        │
        ▼
Aircraft → Flight assignment
```

---

## The Tail Assignment Problem

In airline operations, a flight schedule specifies which flights need to be operated, but an airline must still decide which **specific aircraft tail** will perform each flight.

A valid assignment must satisfy multiple operational constraints.

### Aircraft compatibility

A flight may require a specific aircraft model or aircraft fleet.

The implementation supports both:

- flights with a **pre-assigned aircraft model**;
- flights with a **preferred aircraft fleet**.

For fleet-based assignment, two broad fleet categories are considered:

```text
0 — Narrow-body aircraft
1 — Wide-body aircraft
```

A wide-body aircraft may operate a flight requiring a narrow-body aircraft, but not vice versa.

---

### Seat capacity

An aircraft must provide enough total seats for the passengers booked on the flight.

Assignments that cannot satisfy the required capacity are excluded from the model.

Business-class capacity can also be considered when determining whether an aircraft is feasible for a flight.

---

### Flight overlap

An aircraft cannot operate two flights whose execution intervals overlap.

Conflicting flight-aircraft assignments therefore receive QUBO interactions that prevent them from appearing simultaneously in a low-energy solution.

---

### Flight coverage

A flight should not be assigned to more than one aircraft.

When multiple aircraft are capable of operating a flight, pairwise interactions are introduced between the corresponding decision variables.

---

### Aircraft continuity

Flights assigned to the same aircraft must form a geographically feasible sequence.

For example:

```text
Flight A: LIS → MAD
Flight B: MAD → CDG
```

forms a valid direct connection.

However:

```text
Flight A: LIS → MAD
Flight B: FRA → CDG
```

cannot be operated consecutively by the same aircraft unless intermediate activities provide a feasible path between both flights.

The model therefore considers connectivity between activities and encourages or enforces valid aircraft rotations.

---

### Maintenance feasibility

Aircraft may contain mandatory pre-assigned maintenance activities.

A valid schedule must guarantee that an aircraft:

1. can reach the maintenance airport before the maintenance starts;
2. does not operate an overlapping flight;
3. can continue from the maintenance location to subsequent assigned activities.

Maintenance activities themselves are predetermined and therefore do not need to appear as free binary decision variables in the final optimization model.

Instead, they constrain which flight-aircraft assignments are feasible.

---

## Optimization Approach

The project contains multiple formulations developed during the investigation.

The two main approaches are:

```text
Constraint-based formulation
          │
          ▼
         BQM

and

Direct QUBO formulation
          │
          ▼
         BQM
```

Both ultimately produce a Binary Quadratic Model that can be evaluated by different samplers.

---

## Binary Quadratic Models and QUBO

A QUBO problem can be expressed as:

```text
minimize

E(x) = Σᵢ hᵢxᵢ + Σᵢ<ⱼ Jᵢⱼxᵢxⱼ
```

where:

- `xᵢ ∈ {0, 1}` is a binary decision variable;
- `hᵢ` is the linear bias associated with variable `xᵢ`;
- `Jᵢⱼ` represents the interaction between two variables.

In this project, the variables represent possible aircraft-flight assignments.

The energy function combines:

```text
E(x)
 =
E_constraints(x)
 +
E_objectives(x)
```

Low-energy configurations therefore correspond to assignments that satisfy the operational constraints while also achieving desirable optimization objectives.

---

## Constraint-Based Formulation

The original implementation models the scheduling problem through a **Constraint Satisfaction Problem (CSP)** approach before producing the Binary Quadratic Model.

This formulation explicitly represents logical relationships between aircraft activities.

Examples include:

- mutually incompatible flights;
- maximum one-aircraft-per-flight constraints;
- valid activity connections;
- paths between flights and mandatory maintenance;
- paths between consecutive maintenance activities.

The CSP formulation is retained in the repository to allow comparison with the direct QUBO approach.

It can be selected from the command line using:

```bash
python main.py --csp
```

---

## Direct QUBO Formulation

To reduce model-construction overhead, the project also implements the scheduling constraints directly as a QUBO/BQM without first constructing an intermediate CSP model.

The direct formulation includes several major components.

### 1. Flight overlap

For every pair of flights that cannot be performed by the same aircraft, a positive interaction is introduced between their corresponding binary variables.

Selecting both assignments therefore increases the total energy.

---

### 2. Maximum one aircraft per flight

If multiple aircraft can operate a flight, the corresponding variables receive pairwise penalties so that assigning the same flight to multiple aircraft becomes energetically unfavorable.

---

### 3. Invalid activity pairs

Two flights may individually be valid for an aircraft while being impossible to combine into a feasible aircraft rotation.

Those combinations receive penalties in the QUBO.

---

### 4. Aircraft routing

When two selected activities are not directly connected, the model must encourage or require intermediate flights that create a valid path.

For example:

```text
Flight A
    │
    ▼
Intermediate flight(s)
    │
    ▼
Flight B
```

The model therefore considers the network of possible activities that can connect two selected assignments.

---

### 5. Maintenance connectivity

If an aircraft has mandatory maintenance activities at different airports, the assigned flights must form a path that allows the aircraft to reach every maintenance event.

Flights that cannot participate in a feasible path between maintenance activities can be removed from consideration for that aircraft.

---

## Improved QUBO Formulation

The repository also contains an improved version of the direct QUBO formulation.

The goal is to reduce:

- model construction time;
- the number of generated variables;
- the number of explicit logical constraints.

Instead of explicitly encoding every possible long routing path, the model introduces interactions that encourage each selected flight to be followed by compatible activities.

When the penalty parameters are appropriately tuned, the global low-energy solution is encouraged to form valid aircraft routes without requiring every routing relationship to be represented using additional auxiliary variables.

Maintenance-related routing constraints are also simplified by encouraging assignments that connect appropriately to flights before and after mandatory maintenance activities.

This represents an important part of the research carried out in the project: exploring the trade-off between **model expressiveness**, **BQM size**, and **solution quality**.

---

## Constraint Summary

| Constraint | Purpose |
|---|---|
| Aircraft compatibility | Ensure the aircraft model or fleet is suitable for the flight |
| Seat capacity | Ensure sufficient passenger capacity |
| Business-class capacity | Ensure required premium-seat capacity |
| Flight overlap | Prevent one aircraft from operating overlapping flights |
| Maximum one aircraft per flight | Prevent duplicate flight assignments |
| Activity connectivity | Maintain geographically feasible aircraft rotations |
| Maintenance overlap | Prevent flights from conflicting with mandatory maintenance |
| Maintenance connectivity | Ensure aircraft can reach mandatory maintenance events |
| Fixed assignments | Pre-assign flights that are mandatory for maintaining feasibility |

---

## Preprocessing and Fixed Variables

An important part of the model is removing decisions that do not need to be presented to the optimizer.

Some aircraft-flight combinations can be identified as invalid before the BQM is constructed.

Examples include:

- incompatible aircraft models;
- insufficient total seat capacity;
- insufficient business-class capacity;
- flights that make mandatory maintenance unreachable;
- flights that cannot participate in a valid aircraft route.

Removing these variables reduces the size of the optimization problem.

The opposite situation can also occur.

Some assignments may be logically mandatory.

For example:

```text
Maintenance at airport A
        │
        ▼
     Flight A → B
        │
        ▼
Maintenance at airport B
```

If only one flight can connect two mandatory maintenance activities, that flight may be fixed to `1` for the corresponding aircraft rather than left as an optimization variable.

This preprocessing reduces the search space presented to the solver.

---

## Optimization Objectives

Once feasibility has been represented in the BQM, the model can also optimize the quality of the resulting assignment.

Two main operational objectives are implemented.

---

### Seat Utilization

The model can favor aircraft assignments that minimize unused seat capacity.

For a flight `f` assigned to aircraft `a`:

```text
FreeSeats(f, a)
 =
AircraftCapacity(a) - PassengerDemand(f)
```

Assignments with less unnecessary capacity can be given more favorable biases.

Conceptually:

```text
smaller number of unused seats
            │
            ▼
   more favorable QUBO bias
```

This encourages the optimizer to use aircraft whose size more closely matches passenger demand.

---

### Operating Cost

Aircraft assignments can also be weighted according to estimated operational cost.

The model considers cost components such as:

- departure landing costs;
- arrival landing costs;
- airport handling;
- fuel;
- air traffic control;
- parking;
- aircraft rotation costs.

Assignments with lower relative operating costs receive more favorable QUBO biases.

The corresponding objective parameters determine the relative influence of operational optimization compared with feasibility penalties.

---

## Solvers

One advantage of representing the problem as a Binary Quadratic Model is that the same model can be evaluated using different optimization strategies.

The solver layer includes support for several D-Wave and classical samplers.

| Solver | Approach | Execution |
|---|---|---|
| `DWaveSampler` | Quantum annealing | D-Wave QPU |
| `EmbeddingComposite` | QPU embedding layer | D-Wave QPU |
| `LeapHybridSampler` | Quantum-classical hybrid | D-Wave Leap |
| `KerberosSampler` | Hybrid decomposition | Ocean Hybrid |
| `SimulatedAnnealingSampler` | Classical simulated annealing | Local |
| `TabuSampler` | Tabu search | Local |
| `ExactSolver` | Exhaustive enumeration | Local |

This makes it possible to investigate the same tail-assignment formulation using quantum, hybrid, and classical solution techniques.

`ExactSolver` is primarily useful for very small problem instances because its search space grows exponentially.

---

## Project Structure

```text
quantum-tail-assignment/
│
├── analysis/
│   └── Experiment and result analysis
│
├── data/
│   └── Tail-assignment problem instances
│
├── docs/
│   ├── QUBO_Model_LuisNoitesMartins.pdf.pdf
│   └── Tese_Luis_Noites_Final_2020.07.31.pdf
│
├── src/
│   ├── Loader.py
│   │
│   ├── models/
│   │   └── Domain models for flights, aircraft,
│   │       maintenance activities, airports, etc.
│   │
│   └── scheduler/
│       ├── CSP/
│       │   └── Constraint-based BQM formulation
│       │
│       ├── QUBO/
│       │   └── Direct QUBO formulation
│       │
│       ├── GenericMacros.py
│       ├── ObjectiveFunction.py
│       ├── Scheduler.py
│       ├── Solution.py
│       └── Solver.py
│
├── tests/
│   └── Model and constraint tests
│
├── utils/
│
├── main.py
├── LICENSE
└── README.md
```

---

## Input Data

The problem instances are described using CSV files.

Depending on the scenario, the input directory contains files describing:

| File | Purpose |
|---|---|
| `airports.csv` | Airport information |
| `city_pairs.csv` | Connections between airports |
| `aircraft_models.csv` | Aircraft model characteristics |
| `aircraft.csv` | Individual aircraft |
| `maintenances.csv` | Mandatory aircraft maintenance |
| `model_flights.csv` | Flights containing aircraft-model requirements |
| `fleet_flights.csv` | Flights containing fleet requirements |

The input activities should be chronologically ordered where required by the scheduling logic.

In particular, flights and maintenance activities should be ordered by their start and end times.

Example datasets are available under:

```text
data/
```

---

## Getting Started

### Requirements

The project is implemented in Python and uses the D-Wave Ocean ecosystem.

Core libraries used by the implementation include packages from the D-Wave stack such as:

```text
dimod
dwave-system
dwave-hybrid
dwave-neal
dwave-tabu
```

A **D-Wave Leap account** is required only when executing on D-Wave cloud resources such as a QPU or Leap hybrid solver.

Classical samplers such as simulated annealing, tabu search, and the exact solver can be executed locally.

For current information about installing and configuring the D-Wave Ocean SDK, see:

https://docs.dwavequantum.com/

> **Note**
>
> This repository originated as a research implementation and does not yet use a modern Python dependency manifest such as `pyproject.toml`.
>
> Reproducible dependency management is therefore an area that can be modernized in a future revision of the project.

---

## D-Wave Configuration

To execute problems using D-Wave quantum or Leap hybrid solvers, configure the Ocean SDK with credentials for a D-Wave Leap account.

The standard Ocean configuration workflow can be used:

```bash
dwave setup
```

or:

```bash
dwave config create
```

Follow the official D-Wave documentation for the currently recommended authentication procedure:

https://docs.dwavequantum.com/

Local classical solvers do not require D-Wave cloud credentials.

---

## Usage

The main command-line entry point is:

```bash
python main.py
```

By default, the implementation:

- uses the direct QUBO formulation;
- assumes fleet-based flight requirements;
- reads data from the default configured data directory.

---

### Select an Input Dataset

Use `--filesdirectory`:

```bash
python main.py --filesdirectory data/final/model3
```

The path should point to the directory containing the required CSV input files.

---

### Aircraft Model Assignment

By default, flights are interpreted using aircraft fleet requirements.

To use flights containing explicitly pre-assigned aircraft models:

```bash
python main.py \
  --aircraftmodel \
  --filesdirectory data/final/model3
```

---

### Use the CSP Formulation

The direct QUBO implementation is used by default.

To generate the BQM through the CSP-based formulation:

```bash
python main.py \
  --csp \
  --filesdirectory data/final/model3
```

---

### Print the Assignment Matrix

```bash
python main.py \
  --printmatrix \
  --filesdirectory data/final/model3
```

---

### Export a Solution

```bash
python main.py \
  --export \
  --filesdirectory data/final/model3
```

---

### Export the BQM

The Binary Quadratic Model can be generated and serialized for later solving:

```bash
python main.py \
  --exportbqm \
  --filesdirectory data/final/model3
```

---

### Load an Existing BQM

A previously serialized BQM can be loaded using:

```bash
python main.py \
  --loadbqm path/to/model.json
```

The serialized representation includes metadata describing:

- whether the model was generated using `QUBO` or `CSP`;
- fixed variables;
- model-construction time.

---

### Inspect Solutions by Energy

```bash
python main.py \
  --energysolution \
  --filesdirectory data/final/model3
```

---

### Use an Initial Solution

```bash
python main.py \
  --initialsolution \
  --filesdirectory data/final/model3
```

This mode can be used when an existing assignment is available as a starting point for subsequent optimization.

---

### Additional Options

The CLI also supports options including:

```text
--groupdata
--generatedata
```

Run:

```bash
python main.py --help
```

for the complete set of supported arguments.

---

## Testing

Tests are located under:

```text
tests/
```

The test suite was designed to validate both individual constraints and complete scheduling scenarios.

Conceptually, the tests cover three levels.

### Simple tests

Validate individual scheduling constraints in isolation.

Examples include:

- incompatible assignments;
- overlapping flights;
- maintenance restrictions;
- aircraft-capacity constraints.

### Composed tests

Combine several operational constraints in the same problem instance and verify that a feasible schedule can still be obtained.

### Improved tests

Evaluate optimization behavior rather than only feasibility, including the influence of objective functions on the quality of the selected aircraft assignments.

The project also supports coverage analysis using `coverage.py`.

A typical workflow is:

```bash
coverage run --source=src <test-command>
coverage report
```

or:

```bash
coverage html
```

to generate an HTML coverage report.

---

## Research Documentation

The repository includes additional documentation describing the formulation and the research behind the project.

### QUBO Model

[`docs/QUBO_Model_LuisNoitesMartins.pdf.pdf`](docs/QUBO_Model_LuisNoitesMartins.pdf.pdf)

Contains detailed material about the QUBO representation and optimization model.

### Master's Thesis

[`docs/Tese_Luis_Noites_Final_2020.07.31.pdf`](docs/Tese_Luis_Noites_Final_2020.07.31.pdf)

Contains the broader research work associated with the implementation.

These documents provide considerably more detail about the mathematical formulation, experiments, and research context than is appropriate for the main repository README.

---

## Research Context

The Tail Assignment Problem belongs to a broader class of large combinatorial scheduling problems encountered in airline operations.

Traditional approaches to problems of this type include techniques such as:

- mixed-integer programming;
- constraint programming;
- heuristics;
- metaheuristics;
- decomposition methods.

This project investigates an alternative representation in which operational constraints and optimization objectives are encoded into a Binary Quadratic Model.

That representation is particularly interesting because it enables the same scheduling model to be evaluated through different computational paradigms:

```text
                   Binary Quadratic Model
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Classical         Hybrid          Quantum
      samplers          solvers         annealing
```

The project is therefore not only an implementation of tail assignment, but also an investigation into the applicability of **quantum optimization techniques to real-world airline operations research problems**.

---

## Limitations

This repository should be viewed primarily as a **research and experimental implementation** rather than a production airline scheduling platform.

In particular:

- quantum annealing performance depends strongly on QUBO formulation and penalty tuning;
- larger problem instances may require decomposition or hybrid solving strategies;
- direct QPU execution is constrained by available hardware topology and embedding requirements;
- classical and quantum solver results should be compared carefully rather than assuming quantum advantage;
- the current repository predates modern Python packaging and reproducible dependency-management practices.

These limitations are part of the motivation for the project: understanding how a realistic operational optimization problem behaves when translated into a quantum-compatible formulation.

---

## Potential Future Work

Possible extensions include:

- modernizing dependency management using `pyproject.toml` and `uv`;
- adding reproducible solver benchmarks;
- adding GitHub Actions CI;
- comparing solver performance across classical, hybrid, and QPU approaches;
- documenting QUBO penalty calibration systematically;
- adding larger and more diverse airline scenarios;
- introducing additional operational objectives;
- benchmarking against established classical optimization approaches;
- investigating decomposition strategies for larger tail-assignment instances;
- evaluating newer generations of D-Wave quantum and hybrid optimization technology.

---

## Authors

### Main Author

**Luis Noites Martins**

### Supervisors

**Ana Paula Rocha**

**António J. M. Castro**

---

## License

This project is licensed under the **Apache License 2.0**.

See [`LICENSE`](LICENSE) for details.

---

## Acknowledgements

This project was developed as academic research exploring the intersection of:

**Airline Operations Research × Combinatorial Optimization × Quantum Computing**

It uses the D-Wave Ocean software ecosystem for the formulation and evaluation of Binary Quadratic Models using quantum, hybrid, and classical optimization methods.
