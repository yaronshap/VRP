# 🚚 VRPTW Solver Web Application

A web-based Vehicle Routing Problem with Time Windows (VRPTW) solver using PyVRP and Streamlit.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## Features

- 📊 **Interactive Web Interface**: Upload location data and configure parameters through an intuitive UI
- 🗺️ **Map Visualization**: View locations and optimized routes on interactive maps
- ⚡ **Powerful Optimization**: Built on PyVRP, a high-performance routing solver
- 📥 **Export Results**: Download solutions as JSON and interactive HTML maps
- 🎯 **Preset Examples**: Quick start with pre-configured example problems
- ⏰ **Multi-day Support**: Configure time windows spanning multiple days

## Quick Start

### Running Locally

1. Clone this repository:
```bash
git clone https://github.com/yaronshap/VRP.git
cd VRP
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run vrptw_app.py
```

### Running on Streamlit Cloud

Click the badge above to access the deployed app (no installation needed!)

## How to Use

1. **Upload Location Data**: Upload a CSV file with your locations
   - Required columns: `name`, `address`, `latitude`, `longitude`
   - First row should be the depot (starting point)
   - Sample file: `locations.csv` (198 locations in Rochester, NY)

2. **Configure Parameters**:
   - **Vehicle Settings**: Number of vehicles, capacity per vehicle
   - **Time Settings**: Service time per location, time window (start time + duration)
   - **Optimization**: Average speed, max solving time

3. **Solve**: Click "🎯 Solve VRPTW" to optimize routes

4. **View Results**: 
   - Interactive map showing optimized routes
   - Route metrics (distance, duration, customers served)
   - Export as JSON or HTML

## CSV Format

Your location file should follow this format:

```csv
name,address,latitude,longitude
Rochester City Center,"1 South Clinton Avenue, Rochester, NY 14604",43.154879,-77.608849
Customer 1,"123 Main St, Rochester, NY",43.1566,-77.6088
Customer 2,"456 Park Ave, Rochester, NY",43.1489,-77.5912
```

**Important**: The first row is automatically treated as the depot (starting/ending point).

## Problem Parameters

- **Number of Vehicles**: Total vehicles available (1-100)
- **Vehicle Capacity**: Max customers per vehicle (1-200)
- **Service Time**: Minutes spent at each location (1-240)
- **Time Window**: When services can be performed
  - Start Time: Earliest start time (HH:MM)
  - Duration: Hours and minutes from start (supports multi-day)
- **Average Speed**: Driving speed in mph (10-70)
- **Max Solving Time**: Optimization time limit in seconds (10-300)

## What is VRPTW?

The Vehicle Routing Problem with Time Windows (VRPTW) finds optimal routes for a fleet of vehicles to serve customers, subject to:
- Each customer visited exactly once
- Vehicle capacity constraints
- Time window constraints (all services within specified period)
- Minimize total travel distance

## Technologies Used

- **PyVRP**: High-performance VRP solver
- **Streamlit**: Web application framework
- **Folium**: Interactive map visualization
- **Pandas**: Data manipulation
- **NumPy**: Numerical computations

## Sample Dataset

The included `locations.csv` contains 198 locations in Rochester, NY:
- 1 depot (Rochester City Center)
- 197 hotels in the area

This dataset is perfect for testing and demonstration.

## Output Files

After solving, you can download:
- **JSON**: Complete solution data (routes, distances, timings)
- **HTML**: Interactive map with routes (open in browser)

## Credits

**Created by**: Yaron Shaposhnik  
**Email**: yaron.shaposhnik@simon.rochester.edu  
**Institution**: Simon Business School, University of Rochester  
**Repository**: https://github.com/yaronshap/VRP

## License

This project is for educational purposes.

## Support

For questions or issues:
- Open an issue on GitHub
- Contact: yaron.shaposhnik@simon.rochester.edu

