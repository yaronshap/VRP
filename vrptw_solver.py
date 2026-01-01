"""
VRPTW Solver Module using PyVRP
================================

This module provides a simple interface for solving Vehicle Routing Problems 
with Time Windows (VRPTW) using the PyVRP package.

Example usage:
    from vrptw_solver import solve_vrptw
    
    result = solve_vrptw(
        csv_file='locations.csv',
        num_vehicles=5,
        vehicle_capacity=10,
        service_time=60,
        time_window_start=540,
        time_window_end=1020,
        max_route_duration=480,
        avg_speed_mph=30,
        max_runtime=60,
        output_json='solution.json',
        output_plot='solution.png'
    )
"""

import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import folium
from math import radians, cos, sin, asin, sqrt
from pyvrp import Model
from pyvrp.stop import MaxRuntime


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Returns distance in miles.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in miles
    r = 3956
    return c * r


def compute_distance_matrix(locations_df):
    """
    Compute pairwise distance matrix using Haversine formula.
    
    Parameters
    ----------
    locations_df : pandas.DataFrame
        DataFrame with 'latitude' and 'longitude' columns
        
    Returns
    -------
    numpy.ndarray
        Distance matrix in miles (n x n)
    """
    n = len(locations_df)
    distance_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            dist = haversine_distance(
                locations_df.iloc[i]['latitude'],
                locations_df.iloc[i]['longitude'],
                locations_df.iloc[j]['latitude'],
                locations_df.iloc[j]['longitude']
            )
            distance_matrix[i, j] = dist
            distance_matrix[j, i] = dist
    
    return distance_matrix


def miles_to_minutes(distance_miles, avg_speed_mph=30):
    """Convert distance in miles to travel time in minutes"""
    return int(distance_miles / avg_speed_mph * 60)


def solve_vrptw(csv_file,
                num_vehicles=10,
                vehicle_capacity=20,
                service_time=60,
                time_window_start=540,
                time_window_end=1020,
                max_route_duration=None,
                avg_speed_mph=30,
                max_runtime=60,
                output_json=None,
                output_plot=None,
                num_locations=None):
    """
    Solve a Vehicle Routing Problem with Time Windows (VRPTW).
    
    Parameters
    ----------
    csv_file : str
        Path to CSV file containing locations. Must have columns:
        'name', 'address', 'latitude', 'longitude'
        The first row is treated as the depot.
    num_vehicles : int, default=10
        Number of available vehicles
    vehicle_capacity : int, default=20
        Maximum number of customers per vehicle
    service_time : int, default=60
        Service duration at each customer location (minutes)
    time_window_start : int, default=540
        Earliest service start time (minutes from midnight, 540 = 9am)
    time_window_end : int, default=1020
        Latest service end time (minutes from midnight, 1020 = 5pm)
    max_route_duration : int, optional
        Maximum duration for any single route (minutes). If None, defaults
        to the time window duration (time_window_end - time_window_start)
    avg_speed_mph : int, default=30
        Average driving speed for travel time calculation
    max_runtime : int, default=60
        Maximum solving time in seconds
    output_json : str, optional
        Path to save solution as JSON file
    output_plot : str, optional
        Path to save visualization as image file
    num_locations : int, optional
        If specified, only use the first num_locations from the CSV file
        (useful for testing with smaller datasets)
        
    Returns
    -------
    dict
        Dictionary containing solution details:
        - 'feasible': bool indicating if solution was found
        - 'cost': objective value
        - 'routes': list of routes (each route is a list of location indices)
        - 'num_routes': number of routes used
        - 'total_distance': total distance traveled (miles)
        - 'locations': list of location details
    """
    
    print("="*70)
    print("VRPTW SOLVER")
    print("="*70)
    
    # Load locations from CSV
    print(f"\nLoading locations from: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Select subset if specified
    if num_locations is not None:
        df = df.head(num_locations)
        print(f"Using first {num_locations} locations")
    
    n = len(df)
    print(f"Loaded {n} locations (1 depot + {n-1} customers)")
    
    # Compute distance matrix
    print("Computing distance matrix...")
    distance_matrix = compute_distance_matrix(df)
    
    # Compute duration matrix
    print(f"Computing travel times (average speed: {avg_speed_mph} mph)...")
    duration_matrix = np.zeros_like(distance_matrix, dtype=int)
    for i in range(n):
        for j in range(n):
            duration_matrix[i, j] = miles_to_minutes(distance_matrix[i, j], avg_speed_mph)
    
    # Set default max route duration if not specified
    if max_route_duration is None:
        max_route_duration = time_window_end - time_window_start
    
    # Display problem parameters
    print("\n" + "="*70)
    print("PROBLEM PARAMETERS")
    print("="*70)
    print(f"Locations: {n} (1 depot + {n-1} customers)")
    print(f"Vehicles: {num_vehicles}")
    print(f"Vehicle capacity: {vehicle_capacity} customers")
    print(f"Service time: {service_time} minutes per location")
    print(f"Time window: {time_window_start//60}:{time_window_start%60:02d} - {time_window_end//60}:{time_window_end%60:02d}")
    print(f"Max route duration: {max_route_duration} minutes ({max_route_duration//60}h {max_route_duration%60}m)")
    print(f"Average speed: {avg_speed_mph} mph")
    print(f"Max solving time: {max_runtime} seconds")
    
    # Build PyVRP model
    print("\n" + "="*70)
    print("BUILDING MODEL")
    print("="*70)
    
    m = Model()
    
    # Add depot
    depot = m.add_depot(
        x=int(df.iloc[0]['longitude'] * 100000),
        y=int(df.iloc[0]['latitude'] * 100000),
        tw_early=time_window_start,
        tw_late=time_window_end
    )
    
    # Add customers
    clients = []
    for i in range(1, n):
        client = m.add_client(
            x=int(df.iloc[i]['longitude'] * 100000),
            y=int(df.iloc[i]['latitude'] * 100000),
            delivery=1,
            service_duration=service_time,
            tw_early=time_window_start,
            tw_late=time_window_end,
            name=df.iloc[i]['name']
        )
        clients.append(client)
    
    # Add vehicle type
    vehicle_type = m.add_vehicle_type(
        num_available=num_vehicles,
        capacity=vehicle_capacity,
        name=f"Vehicle"
    )
    
    # Add edges
    print("Adding edges...")
    
    # Depot to all clients
    for j in range(1, n):
        distance = int(distance_matrix[0][j] * 100)  # Convert to cm
        duration = duration_matrix[0][j]
        m.add_edge(depot, clients[j-1], distance=distance, duration=duration)
        m.add_edge(clients[j-1], depot, distance=distance, duration=duration)
    
    # Between all clients
    for i in range(1, n):
        for j in range(i+1, n):
            distance = int(distance_matrix[i][j] * 100)  # Convert to cm
            duration = duration_matrix[i][j]
            m.add_edge(clients[i-1], clients[j-1], distance=distance, duration=duration)
            m.add_edge(clients[j-1], clients[i-1], distance=distance, duration=duration)
    
    # Solve
    print("\n" + "="*70)
    print("SOLVING")
    print("="*70)
    print("Running optimization algorithm...")
    
    result = m.solve(stop=MaxRuntime(max_runtime), display=False)
    
    # Process results
    print("\n" + "="*70)
    print("SOLUTION")
    print("="*70)
    
    solution_data = {
        'feasible': result.is_feasible(),
        'cost': result.cost() if result.is_feasible() else None,
        'routes': [],
        'num_routes': 0,
        'total_distance': 0,
        'total_duration': 0,
        'locations': df.to_dict('records')
    }
    
    if not result.is_feasible():
        print("\nNo feasible solution found!")
        print("\nPossible reasons:")
        print("  - Time window too tight for the number of customers")
        print("  - Vehicle capacity too small")
        print("  - Not enough vehicles")
        print("  - Max route duration too restrictive")
        print("\nTry adjusting parameters:")
        print("  - Increase number of vehicles")
        print("  - Increase vehicle capacity")
        print("  - Extend time window")
        print("  - Reduce service time")
        print("  - Increase max_route_duration")
        return solution_data
    
    print(f"\nStatus: FEASIBLE")
    print(f"Objective value: {result.cost():.2f}")
    
    routes = result.best.routes()
    
    # Process each route
    for route in routes:
        visits = route.visits()
        if len(visits) == 0:
            continue
        
        route_data = {
            'visits': [int(v) for v in visits],
            'locations': [df.iloc[0]['name']] + [df.iloc[int(i)]['name'] for i in visits] + [df.iloc[0]['name']],
            'distance': 0,
            'duration': 0
        }
        
        # Calculate route distance and duration
        current = 0
        for visit in visits:
            visit = int(visit)
            route_data['distance'] += float(distance_matrix[current][visit])
            route_data['duration'] += int(duration_matrix[current][visit] + service_time)
            current = visit
        route_data['distance'] += float(distance_matrix[current][0])
        route_data['duration'] += int(duration_matrix[current][0])
        
        solution_data['routes'].append(route_data)
        solution_data['total_distance'] += route_data['distance']
        solution_data['total_duration'] += route_data['duration']
    
    solution_data['num_routes'] = len(solution_data['routes'])
    
    # Print summary
    print(f"Number of routes: {solution_data['num_routes']}")
    print(f"Total distance: {solution_data['total_distance']:.2f} miles")
    print(f"Total duration: {solution_data['total_duration']} minutes ({solution_data['total_duration']//60}h {solution_data['total_duration']%60}m)")
    print(f"Average route distance: {solution_data['total_distance']/solution_data['num_routes']:.2f} miles")
    
    customers_served = sum(len(r['visits']) for r in solution_data['routes'])
    print(f"Customers served: {customers_served} / {n-1}")
    
    # Print routes
    print("\n" + "="*70)
    print("ROUTES")
    print("="*70)
    for i, route_data in enumerate(solution_data['routes'], 1):
        print(f"\nRoute {i}:")
        print(f"  Customers: {len(route_data['visits'])}")
        print(f"  Distance: {route_data['distance']:.2f} miles")
        print(f"  Duration: {route_data['duration']} minutes ({route_data['duration']//60}h {route_data['duration']%60}m)")
        print(f"  Path: {' -> '.join(route_data['locations'])}")
    
    # Save to JSON if requested
    if output_json:
        print(f"\nSaving solution to: {output_json}")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(solution_data, f, indent=2)
    
    # Create visualization if requested
    if output_plot:
        print(f"Creating visualization: {output_plot}")
        visualize_solution(df, solution_data, output_plot)
    
    return solution_data


def visualize_solution(locations_df, solution_data, output_file):
    """
    Create an interactive map visualization of the VRPTW solution using Folium.
    
    Parameters
    ----------
    locations_df : pandas.DataFrame
        DataFrame with location information (must include 'name', 'address', 'latitude', 'longitude')
    solution_data : dict
        Solution data from solve_vrptw
    output_file : str
        Path to save the HTML map (e.g., 'solution_map.html')
    """
    if not solution_data['feasible']:
        print("Cannot visualize: no feasible solution found")
        return
    
    # Calculate center of map
    center_lat = locations_df['latitude'].mean()
    center_lon = locations_df['longitude'].mean()
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # Color palette for routes (Folium color names)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
              'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray',
              'black', 'lightgray']
    
    # Add depot marker (with home icon)
    folium.Marker(
        location=[locations_df.iloc[0]['latitude'], locations_df.iloc[0]['longitude']],
        popup=f"<b>DEPOT</b><br>{locations_df.iloc[0]['name']}",
        tooltip="Depot (Start/End)",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)
    
    # Plot each route
    for route_idx, route_data in enumerate(solution_data['routes']):
        color = colors[route_idx % len(colors)]
        visits = [0] + route_data['visits'] + [0]  # Include depot at start and end
        
        # Create route line
        route_coords = [[locations_df.iloc[v]['latitude'], 
                        locations_df.iloc[v]['longitude']] for v in visits]
        
        folium.PolyLine(
            route_coords,
            color=color,
            weight=3,
            opacity=0.8,
            popup=f"<b>Route {route_idx + 1}</b><br>"
                  f"Customers: {len(route_data['visits'])}<br>"
                  f"Distance: {route_data['distance']:.1f} miles<br>"
                  f"Duration: {route_data['duration']} min"
        ).add_to(m)
        
        # Add customer markers (circles)
        for idx, customer_idx in enumerate(route_data['visits'], 1):
            folium.CircleMarker(
                location=[locations_df.iloc[customer_idx]['latitude'],
                         locations_df.iloc[customer_idx]['longitude']],
                radius=6,
                popup=f"<b>Route {route_idx + 1}, Stop {idx}</b><br>"
                      f"{locations_df.iloc[customer_idx]['name']}<br>"
                      f"{locations_df.iloc[customer_idx]['address']}",
                tooltip=f"R{route_idx+1}-{idx}: {locations_df.iloc[customer_idx]['name']}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 280px; height: auto;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; border-bottom: 2px solid #333; padding-bottom: 5px;">VRPTW Solution</h4>
        <p style="margin: 5px 0;"><b>Routes:</b> {solution_data["num_routes"]}<br>
        <b>Total Distance:</b> {solution_data["total_distance"]:.1f} miles<br>
        <b>Total Duration:</b> {solution_data["total_duration"]} min ({solution_data["total_duration"]//60}h {solution_data["total_duration"]%60}m)<br>
        <b>Customers:</b> {sum(len(r["visits"]) for r in solution_data["routes"])}</p>
        <hr style="margin: 8px 0;">
    '''
    
    for i in range(solution_data["num_routes"]):
        color = colors[i % len(colors)]
        legend_html += f'<p style="margin:4px 0; font-size:12px;"><span style="color:{color}; font-size:18px;">●</span> <b>Route {i+1}:</b> '
        legend_html += f'{len(solution_data["routes"][i]["visits"])} stops, '
        legend_html += f'{solution_data["routes"][i]["distance"]:.1f} mi</p>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    m.save(output_file)
    print(f"Visualization saved to: {output_file}")
    print("(Open the HTML file in a web browser to view the interactive map)")
    
    return m


if __name__ == "__main__":
    # Example usage
    solution = solve_vrptw(
        csv_file='hotel_data/rochester_hotels_filtered.csv',
        num_vehicles=10,
        vehicle_capacity=5,
        service_time=60,
        time_window_start=540,
        time_window_end=1020,
        max_route_duration=420,
        avg_speed_mph=30,
        max_runtime=60,
        output_json='hotel_data/vrptw_solution.json',
        output_plot='hotel_data/vrptw_solution.html',  # Changed to .html for interactive map
        num_locations=30  # Use only first 30 locations for demo
    )

