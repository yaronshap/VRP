"""
VRPTW Solver - Streamlit App
Interactive web application for solving Vehicle Routing Problems with Time Windows
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
from io import BytesIO
import streamlit.components.v1 as components

# Import the solver
from vrptw_solver import solve_vrptw

# Set page config
st.set_page_config(
    page_title="VRPTW Solver",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make sidebar wider and hide file uploader details
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            width: 400px !important;
        }
        /* Hide the file size and type text */
        [data-testid="stFileUploader"] small {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for solution storage
if 'solution_data' not in st.session_state:
    st.session_state.solution_data = None
if 'solution_html' not in st.session_state:
    st.session_state.solution_html = None
if 'solution_json' not in st.session_state:
    st.session_state.solution_json = None
if 'params_set' not in st.session_state:
    st.session_state.params_set = False
if 'solving' not in st.session_state:
    st.session_state.solving = False

# Title and description
st.title("🚚 Vehicle Routing Problem with Time Windows (VRPTW) Solver")
st.markdown("""
This application solves the Vehicle Routing Problem with Time Windows using PyVRP.
Upload your location data, configure parameters in the sidebar, and get optimized routes!
""")

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Problem Configuration")

# File upload in sidebar (moved to top)
st.sidebar.subheader("📁 Upload Location Data")

uploaded_file = st.sidebar.file_uploader(
    "Choose CSV file",
    type=['csv'],
    help="CSV must contain: name, address, latitude, longitude",
    label_visibility="collapsed"
)

# Show format info
with st.sidebar.expander("ℹ️ CSV Format"):
    st.markdown("""
    **Required columns:**
    - `name`
    - `address`
    - `latitude`
    - `longitude`
    
    **First row = depot**
    """)

# Limit locations widget right after file upload (only show if file uploaded)
if uploaded_file is not None:
    num_locations = st.sidebar.number_input(
        "Limit Locations (0 = all)",
        min_value=0,
        max_value=1000,
        value=st.session_state.get('num_locations', 0),
        help="Use only first N locations (0 = use all)",
        key="num_locs_input"
    )
else:
    num_locations = 0

st.sidebar.markdown("---")

# Parameters in sidebar (only show if file uploaded)
if uploaded_file is not None:
    st.sidebar.subheader("🚗 Vehicle Settings")
    num_vehicles = st.sidebar.number_input(
        "Number of Vehicles",
        min_value=1,
        max_value=100,
        value=st.session_state.get('num_vehicles', 5),
        help="Total number of available vehicles"
    )

    vehicle_capacity = st.sidebar.number_input(
        "Vehicle Capacity (customers)",
        min_value=1,
        max_value=200,
        value=st.session_state.get('vehicle_capacity', 99),
        help="Maximum number of customers each vehicle can serve"
    )

    st.sidebar.subheader("⏰ Time Settings")
    service_time = st.sidebar.number_input(
        "Service Time (minutes)",
        min_value=1,
        max_value=240,
        value=st.session_state.get('service_time', 60),
        help="Time spent at each customer location"
    )

    # Time window inputs using time_input widget
    st.sidebar.markdown("**Time Window:**")

    from datetime import time, timedelta

    # Get stored values or defaults
    default_start_hour = st.session_state.get('tw_start_hour', 9)
    default_start_min = st.session_state.get('tw_start_min', 0)
    
    # Get duration (default 8 hours if not set)
    default_duration_hours = st.session_state.get('tw_duration_hours', 8)
    default_duration_mins = st.session_state.get('tw_duration_mins', 0)

    tw_start = st.sidebar.time_input(
        "Start Time",
        value=time(default_start_hour, default_start_min),
        help="Earliest time vehicles can start servicing customers"
    )

    # Duration inputs (allows multi-day windows)
    st.sidebar.markdown("**Duration from Start:**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        duration_hours = st.number_input(
            "Hours",
            min_value=0,
            max_value=168,  # Up to 7 days
            value=default_duration_hours,
            help="Hours from start time",
            key="duration_h"
        )
    with col2:
        duration_mins = st.number_input(
            "Minutes",
            min_value=0,
            max_value=59,
            value=default_duration_mins,
            help="Minutes from start time",
            key="duration_m"
        )
    
    # Store duration in session state
    st.session_state.tw_duration_hours = duration_hours
    st.session_state.tw_duration_mins = duration_mins
    
    # Calculate end time (can span multiple days)
    time_window_start = tw_start.hour * 60 + tw_start.minute
    total_duration_minutes = duration_hours * 60 + duration_mins
    time_window_end = time_window_start + total_duration_minutes
    
    # Calculate and display total duration
    total_hours = total_duration_minutes // 60
    total_mins = total_duration_minutes % 60
    days = total_hours // 24
    hours_in_day = total_hours % 24
    
    if days > 0:
        duration_text = f"{days} day(s), {hours_in_day}h {total_mins}m"
    else:
        duration_text = f"{total_hours}h {total_mins}m"
    
    st.sidebar.info(f"⏰ Total Duration: {duration_text}")

    # Average speed (for travel time calculations)
    avg_speed_mph = st.sidebar.slider(
        "Average Speed (mph)",
        min_value=10,
        max_value=70,
        value=st.session_state.get('avg_speed_mph', 30),
        help="Average driving speed for travel time calculations"
    )

    st.sidebar.subheader("🎯 Optimization Settings")
    max_runtime = st.sidebar.slider(
        "Max Solving Time (seconds)",
        min_value=10,
        max_value=300,
        value=st.session_state.get('max_runtime', 60),
        help="Maximum time allowed for optimization"
    )

    st.sidebar.markdown("---")

    # Solve button in sidebar
    solve_button = st.sidebar.button(
        "🎯 Solve VRPTW", 
        type="primary", 
        use_container_width=True, 
        disabled=(uploaded_file is None or st.session_state.solving)
    )

    # Status placeholder right below solve button
    status_placeholder = st.sidebar.empty()
    progress_placeholder = st.sidebar.empty()

    st.sidebar.markdown("---")

    # Preset buttons at bottom of sidebar
    st.sidebar.subheader("📋 Load Preset Parameters")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.sidebar.button("📝 Example 1", use_container_width=True, help="Small problem: 20 locations, 60-min service"):
            st.session_state.num_vehicles = 5
            st.session_state.vehicle_capacity = 5
            st.session_state.service_time = 60
            st.session_state.tw_start_hour = 9
            st.session_state.tw_start_min = 0
            st.session_state.tw_duration_hours = 8  # 9am to 5pm = 8 hours
            st.session_state.tw_duration_mins = 0
            st.session_state.avg_speed_mph = 30
            st.session_state.max_runtime = 30
            st.session_state.num_locations = 20
            st.session_state.params_set = True
            st.rerun()

    with col2:
        if st.sidebar.button("📝 Example 2", use_container_width=True, help="30 locations, 30-min service"):
            st.session_state.num_vehicles = 5
            st.session_state.vehicle_capacity = 8
            st.session_state.service_time = 30
            st.session_state.tw_start_hour = 9
            st.session_state.tw_start_min = 0
            st.session_state.tw_duration_hours = 8  # 9am to 5pm = 8 hours
            st.session_state.tw_duration_mins = 0
            st.session_state.avg_speed_mph = 30
            st.session_state.max_runtime = 30
            st.session_state.num_locations = 30
            st.session_state.params_set = True
            st.rerun()

    if st.session_state.params_set:
        st.sidebar.success("✓ Preset loaded!")
else:
    # Set defaults when no file uploaded
    num_vehicles = 5
    vehicle_capacity = 99
    service_time = 60
    time_window_start = 540
    time_window_end = 1020
    avg_speed_mph = 30
    max_runtime = 60
    solve_button = False
    status_placeholder = st.sidebar.empty()
    progress_placeholder = st.sidebar.empty()

st.sidebar.markdown("---")

# Credits section at bottom
st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px; font-size: 0.85em; color: #666;'>
        <p style='margin: 5px 0;'><b>🚚 VRPTW Solver</b></p>
        <p style='margin: 5px 0;'>Created by: <b>Yaron Shaposhnik</b></p>
        <p style='margin: 5px 0;'><a href='mailto:yaron.shaposhnik@simon.rochester.edu'>yaron.shaposhnik@simon.rochester.edu</a></p>
        <p style='margin: 15px 0 5px 0; font-size: 0.9em;'>Built with:</p>
        <p style='margin: 5px 0;'><a href='https://streamlit.io' target='_blank'>Streamlit</a> • 
        <a href='https://pyvrp.org' target='_blank'>PyVRP</a> • 
        <a href='https://python-visualization.github.io/folium/' target='_blank'>Folium</a></p>
    </div>
    """, unsafe_allow_html=True)


# ==================== MAIN CONTENT AREA ====================

# Preview uploaded data
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Apply location limit if specified
        if num_locations > 0 and num_locations < len(df):
            df_display = df.head(num_locations)
            locations_note = f" (showing first {num_locations})"
        else:
            df_display = df
            locations_note = ""
        
        # Validate columns
        required_cols = ['name', 'address', 'latitude', 'longitude']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        else:
            # Additional validation
            validation_passed = True
            error_messages = []
            
            # Check for minimum rows
            if len(df_display) < 2:
                error_messages.append("❌ File must contain at least 2 rows (1 depot + 1 customer)")
                validation_passed = False
            
            # Check latitude/longitude are numeric
            try:
                df_display['latitude'] = pd.to_numeric(df_display['latitude'])
                df_display['longitude'] = pd.to_numeric(df_display['longitude'])
            except:
                error_messages.append("❌ Latitude and longitude must be numeric values")
                validation_passed = False
            
            # Check latitude/longitude are in valid ranges
            if validation_passed:
                if not df_display['latitude'].between(-90, 90).all():
                    error_messages.append("❌ Latitude values must be between -90 and 90")
                    validation_passed = False
                if not df_display['longitude'].between(-180, 180).all():
                    error_messages.append("❌ Longitude values must be between -180 and 180")
                    validation_passed = False
            
            # Check for missing values
            if validation_passed and df_display[required_cols].isnull().any().any():
                error_messages.append("❌ Some required fields contain missing values")
                validation_passed = False
            
            # Display validation results
            if not validation_passed:
                for msg in error_messages:
                    st.error(msg)
            else:
                st.success(f"✅ Loaded {len(df_display)} locations{locations_note} (1 depot + {len(df_display)-1} customers)")
                
                # View toggle buttons
                if st.session_state.solution_data is not None:
                    st.subheader("📊 View")
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        view_locations = st.button("📍 Locations", use_container_width=True)
                    with col2:
                        view_solution = st.button("🗺️ Solution", use_container_width=True, type="primary")
                    
                    # Initialize view state if not exists
                    if 'current_view' not in st.session_state:
                        st.session_state.current_view = 'locations'
                    
                    # Update view based on button clicks
                    if view_locations:
                        st.session_state.current_view = 'locations'
                    if view_solution:
                        st.session_state.current_view = 'solution'
                    
                    st.markdown("---")
                    
                    # Display appropriate view
                    if st.session_state.current_view == 'solution':
                        # Display solution
                        if st.session_state.solution_data['feasible']:
                            st.success("✅ Solution Found!")
                            
                            # Summary metrics
                            st.subheader("📊 Solution Summary")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Routes", st.session_state.solution_data['num_routes'])
                            with col2:
                                st.metric("Total Distance", f"{st.session_state.solution_data['total_distance']:.1f} mi")
                            with col3:
                                st.metric("Total Duration", f"{st.session_state.solution_data['total_duration']//60}h {st.session_state.solution_data['total_duration']%60}m")
                            with col4:
                                st.metric("Customers Served", sum(len(r['visits']) for r in st.session_state.solution_data['routes']))
                            
                            # Route details
                            st.subheader("🗺️ Route Details")
                            for i, route in enumerate(st.session_state.solution_data['routes'], 1):
                                with st.expander(f"Route {i}: {len(route['visits'])} customers, {route['distance']:.1f} miles"):
                                    st.write(f"**Duration:** {route['duration']//60}h {route['duration']%60}m")
                                    st.write(f"**Path:** {' → '.join(route['locations'])}")
                            
                            # Display map
                            st.subheader("🗺️ Interactive Solution Map")
                            components.html(st.session_state.solution_html, height=600, scrolling=True)
                            
                            # Download buttons
                            st.subheader("💾 Download Results")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.download_button(
                                    label="📄 Download JSON",
                                    data=st.session_state.solution_json,
                                    file_name="vrptw_solution.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            
                            with col2:
                                st.download_button(
                                    label="🗺️ Download Map (HTML)",
                                    data=st.session_state.solution_html,
                                    file_name="vrptw_map.html",
                                    mime="text/html",
                                    use_container_width=True
                                )
                    else:
                        # Display location map (current view)
                        st.subheader("📍 Location Map")
                        
                        # Create and display location visualization
                        import folium
                        from streamlit_folium import folium_static
                        
                        # Calculate center of map
                        center_lat = df_display['latitude'].mean()
                        center_lon = df_display['longitude'].mean()
                        
                        # Create map
                        m = folium.Map(
                            location=[center_lat, center_lon],
                            zoom_start=11,
                            tiles='OpenStreetMap'
                        )
                        
                        # Add depot marker (first location) with special icon
                        folium.Marker(
                            location=[df_display.iloc[0]['latitude'], df_display.iloc[0]['longitude']],
                            popup=f"<b>🏠 DEPOT</b><br>{df_display.iloc[0]['name']}<br>{df_display.iloc[0]['address']}",
                            tooltip="Depot (Start/End Point)",
                            icon=folium.Icon(color='red', icon='home', prefix='fa')
                        ).add_to(m)
                        
                        # Add customer markers (remaining locations)
                        for idx in range(1, len(df_display)):
                            folium.CircleMarker(
                                location=[df_display.iloc[idx]['latitude'], df_display.iloc[idx]['longitude']],
                                radius=6,
                                popup=f"<b>Customer {idx}</b><br>{df_display.iloc[idx]['name']}<br>{df_display.iloc[idx]['address']}",
                                tooltip=f"Customer {idx}: {df_display.iloc[idx]['name']}",
                                color='blue',
                                fill=True,
                                fillColor='blue',
                                fillOpacity=0.6
                            ).add_to(m)
                        
                        # Display the map
                        folium_static(m, width=800, height=500)
                        
                        # Show data preview
                        with st.expander(f"📋 Data Table ({len(df_display)} locations)"):
                            st.dataframe(df_display, use_container_width=True)
                else:
                    # No solution yet, just show locations
                    st.subheader("📍 Location Map")
                    
                    import folium
                    from streamlit_folium import folium_static
                    
                    # Calculate center of map
                    center_lat = df_display['latitude'].mean()
                    center_lon = df_display['longitude'].mean()
                    
                    # Create map
                    m = folium.Map(
                        location=[center_lat, center_lon],
                        zoom_start=11,
                        tiles='OpenStreetMap'
                    )
                    
                    # Add depot marker
                    folium.Marker(
                        location=[df_display.iloc[0]['latitude'], df_display.iloc[0]['longitude']],
                        popup=f"<b>🏠 DEPOT</b><br>{df_display.iloc[0]['name']}<br>{df_display.iloc[0]['address']}",
                        tooltip="Depot (Start/End Point)",
                        icon=folium.Icon(color='red', icon='home', prefix='fa')
                    ).add_to(m)
                    
                    # Add customer markers
                    for idx in range(1, len(df_display)):
                        folium.CircleMarker(
                            location=[df_display.iloc[idx]['latitude'], df_display.iloc[idx]['longitude']],
                            radius=6,
                            popup=f"<b>Customer {idx}</b><br>{df_display.iloc[idx]['name']}<br>{df_display.iloc[idx]['address']}",
                            tooltip=f"Customer {idx}: {df_display.iloc[idx]['name']}",
                            color='blue',
                            fill=True,
                            fillColor='blue',
                            fillOpacity=0.6
                        ).add_to(m)
                    
                    # Display the map
                    folium_static(m, width=800, height=500)
                    
                    # Show data preview
                    with st.expander(f"📋 Data Table ({len(df_display)} locations)"):
                        st.dataframe(df_display, use_container_width=True)
                
                # Check if solve button was clicked
                if solve_button:
                    # Clear previous solution and switch to locations view
                    st.session_state.solution_data = None
                    st.session_state.solution_json = None
                    st.session_state.solution_html = None
                    st.session_state.current_view = 'locations'
                    
                    # Validate time window
                    if time_window_end <= time_window_start:
                        st.error("❌ End time must be after start time!")
                    else:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp_file:
                            df.to_csv(tmp_file.name, index=False)
                            tmp_csv_path = tmp_file.name
                        
                        # Create temp files for outputs
                        tmp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                        tmp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
                        tmp_json.close()
                        tmp_html.close()
                        
                        try:
                            # Set solving state
                            st.session_state.solving = True
                            
                            # Show status in sidebar
                            status_placeholder.info("🔄 Optimizing routes... Please wait...")
                            
                            # Progress bar
                            progress_bar = progress_placeholder.progress(0)
                            
                            # Solve in a thread while updating progress
                            import time
                            import threading
                            
                            solution_result = [None]
                            exception_result = [None]
                            
                            def solve_thread():
                                try:
                                    solution_result[0] = solve_vrptw(
                                        csv_file=tmp_csv_path,
                                        num_vehicles=num_vehicles,
                                        vehicle_capacity=vehicle_capacity,
                                        service_time=service_time,
                                        time_window_start=time_window_start,
                                        time_window_end=time_window_end,
                                        avg_speed_mph=avg_speed_mph,
                                        max_runtime=max_runtime,
                                        output_json=tmp_json.name,
                                        output_plot=tmp_html.name,
                                        num_locations=num_locations if num_locations > 0 else None
                                    )
                                except Exception as e:
                                    exception_result[0] = e
                            
                            # Start solving thread
                            thread = threading.Thread(target=solve_thread)
                            thread.start()
                            
                            # Update progress bar
                            start_time = time.time()
                            while thread.is_alive():
                                elapsed = time.time() - start_time
                                progress = min(elapsed / max_runtime, 0.99)
                                progress_bar.progress(progress)
                                time.sleep(0.1)
                            
                            thread.join()
                            
                            # Complete progress
                            progress_bar.progress(1.0)
                            
                            # Check for exceptions
                            if exception_result[0]:
                                raise exception_result[0]
                            
                            solution = solution_result[0]
                            
                            # Clear status and progress
                            status_placeholder.empty()
                            progress_placeholder.empty()
                            
                            # Reset solving state
                            st.session_state.solving = False
                            
                            # Check if solution is feasible
                            if not solution['feasible']:
                                st.error("❌ No feasible solution found!")
                                st.markdown("""
                                ### Suggestions:
                                - Increase the number of vehicles
                                - Increase vehicle capacity
                                - Extend the time window
                                - Reduce service time
                                - Use fewer locations
                                """)
                            else:
                                # Store solution in session state
                                st.session_state.solution_data = solution
                                with open(tmp_html.name, 'r', encoding='utf-8') as f:
                                    st.session_state.solution_html = f.read()
                                with open(tmp_json.name, 'r') as f:
                                    st.session_state.solution_json = f.read()
                                
                                # Switch to solution view
                                st.session_state.current_view = 'solution'
                                
                                # Rerun to update the display
                                st.rerun()
                        
                        except Exception as e:
                            st.session_state.solving = False
                            status_placeholder.empty()
                            progress_placeholder.empty()
                            st.error(f"❌ Error solving problem: {str(e)}")
                        
                        finally:
                            # Reset solving state and clear UI
                            st.session_state.solving = False
                            status_placeholder.empty()
                            progress_placeholder.empty()
                            # Cleanup temp files
                            try:
                                os.unlink(tmp_csv_path)
                                os.unlink(tmp_json.name)
                                os.unlink(tmp_html.name)
                            except:
                                pass
    
    except Exception as e:
        st.error(f"❌ Error loading CSV file: {str(e)}")

else:
    # Show simple message when no file uploaded
    st.info("👈 Please upload a CSV file in the sidebar to begin")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with PyVRP and Streamlit | 🚚 VRPTW Solver</p>
</div>
""", unsafe_allow_html=True)

