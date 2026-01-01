#!/bin/bash
# Quick start script for VRPTW Streamlit App

echo "Starting VRPTW Solver Web Application..."
echo ""

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo ""
elif [ -f "venv/Scripts/activate" ]; then
    echo "Activating virtual environment..."
    source venv/Scripts/activate
    echo ""
else
    echo "Warning: Virtual environment not found"
    echo "Using system Python..."
    echo ""
fi

echo "The app will open in your default browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run vrptw_app.py


