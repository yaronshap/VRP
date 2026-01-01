# VRPTW Solver Module

A Python module for solving Vehicle Routing Problems with Time Windows (VRPTW) using PyVRP.

## Overview

This module provides a simple interface for solving VRPTW problems. It's designed for educational purposes, allowing students to experiment with different problem parameters and visualize solutions.

## Features

- **Easy-to-use interface**: Single function call to solve VRPTW problems
- **Automatic distance calculation**: Computes distances between locations using Haversine formula
- **Flexible parameters**: Customize vehicles, capacity, time windows, service times, etc.
- **Solution export**: Save solutions as JSON files
- **Interactive map visualization**: Generate HTML maps with real map tiles showing routes on actual streets
- **Subset selection**: Test with smaller datasets using `num_locations` parameter

## Installation

```bash
pip install -r requirements.txt
```

Required packages:
- `pyvrp` - The optimization solver
- `pandas` - Data handling
- `numpy` - Numerical computations
- `folium` - Interactive map visualization
- `jupyter` - For running the demo notebook

## Usage

### Basic Example

```python
from vrptw_solver import solve_vrptw

solution = solve_vrptw(
    csv_file='hotel_data/rochester_hotels_filtered.csv',
    num_vehicles=5,
    vehicle_capacity=10,
    service_time=60,
    time_window_start=540,    # 9am
    time_window_end=1020,     # 5pm
    max_route_duration=420,   # 7 hours
    avg_speed_mph=30,
    max_runtime=60,
    output_json='solution.json',
    output_plot='solution.html',      # Saves interactive HTML map
    num_locations=20          # Use only first 20 locations
)

if solution['feasible']:
    print(f"Found solution with {solution['num_routes']} routes")
    print(f"Total distance: {solution['total_distance']:.2f} miles")
else:
    print("No feasible solution found")
```

### CSV File Format

The CSV file must contain the following columns:
- `name`: Location name
- `address`: Location address
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate

**Important**: The first row is treated as the depot (starting point for all vehicles).

## Parameters

### Required
- `csv_file` (str): Path to CSV file with location data

### Optional
- `num_vehicles` (int, default=10): Number of available vehicles
- `vehicle_capacity` (int, default=20): Maximum customers per vehicle
- `service_time` (int, default=60): Service duration at each location (minutes)
- `time_window_start` (int, default=540): Earliest service start time (minutes from midnight)
- `time_window_end` (int, default=1020): Latest service end time (minutes from midnight)
- `max_route_duration` (int, optional): Maximum duration for any route (minutes)
- `avg_speed_mph` (int, default=30): Average driving speed for travel time calculations
- `max_runtime` (int, default=60): Maximum solving time (seconds)
- `output_json` (str, optional): Path to save solution JSON (contains complete optimization results)
- `output_plot` (str, optional): Path to save visualization (e.g., 'map.html' for interactive map)
- `num_locations` (int, optional): Use only first N locations (for testing)

## Time Formats

Time windows and durations use "minutes from midnight":
- 6:00 AM = 360 minutes
- 8:00 AM = 480 minutes
- 9:00 AM = 540 minutes
- 12:00 PM = 720 minutes
- 5:00 PM = 1020 minutes
- 6:00 PM = 1080 minutes

## Solution Structure

The function returns a dictionary with:
```python
{
    'feasible': bool,              # Whether a solution was found
    'cost': float,                 # Objective value
    'num_routes': int,             # Number of routes used
    'total_distance': float,       # Total distance (miles)
    'total_duration': int,         # Total duration (minutes)
    'routes': [                    # List of routes
        {
            'visits': [1, 3, 5],   # Customer indices visited
            'locations': ['Depot', 'A', 'B', 'Depot'],
            'distance': 42.5,      # Route distance (miles)
            'duration': 250        # Route duration (minutes)
        },
        ...
    ],
    'locations': [...]             # Original location data
}
```

**Note**: When `output_json` is specified, the complete optimization results (including all route sequences, customer visits, distances, and durations) are saved to the JSON file. This is useful for:
- Detailed analysis of the solution
- Importing into other tools
- Comparing different solutions
- Verifying route details

## Demo Notebook

See `vrptw_demo.ipynb` for interactive examples including:
- Small and medium-sized problems
- Parameter experimentation
- Solution comparison
- Student exercises

## Tips for Finding Feasible Solutions

If the solver can't find a feasible solution, try:

1. **Increase number of vehicles**: More vehicles = more capacity
2. **Increase vehicle capacity**: Each vehicle can serve more customers
3. **Extend time window**: Longer workday allows more flexibility
4. **Reduce service time**: Faster service = more customers per route
5. **Increase max_route_duration**: Allow longer routes
6. **Use fewer locations**: Start small and scale up

## Example Scenarios

### Scenario 1: Many Small Routes
```python
solve_vrptw(..., num_vehicles=20, vehicle_capacity=3, ...)
```

### Scenario 2: Few Large Routes
```python
solve_vrptw(..., num_vehicles=5, vehicle_capacity=15, ...)
```

### Scenario 3: Quick Service
```python
solve_vrptw(..., service_time=30, vehicle_capacity=10, ...)
```

### Scenario 4: Extended Hours
```python
solve_vrptw(..., time_window_start=480, time_window_end=1080, ...)  # 8am-6pm
```

## Troubleshooting

**Problem**: "No feasible solution found"
- Solution: Adjust parameters as described above

**Problem**: Solution is very expensive (high cost)
- Solution: Increase `max_runtime` to give the solver more time

**Problem**: Some customers not served
- Solution: Increase vehicles or capacity, or extend time windows

**Problem**: Routes violate time constraints
- Solution: The solver respects time windows; if a solution is feasible, constraints are satisfied

## Educational Use

This module is designed for teaching optimization concepts. Students can:
1. Experiment with different parameter combinations
2. Understand trade-offs (e.g., more vehicles vs. longer routes)
3. Visualize routing decisions
4. Analyze solution quality
5. Compare different scenarios

## License

This module is provided for educational purposes.

