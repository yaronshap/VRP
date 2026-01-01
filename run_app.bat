@echo off
REM Quick start script for VRPTW Streamlit App (Windows)

echo Starting VRPTW Solver Web Application...
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
) else (
    echo Warning: Virtual environment not found at venv\Scripts\activate.bat
    echo Using system Python...
    echo.
)

echo The app will open in your default browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

streamlit run vrptw_app.py

REM Deactivate on exit
if exist "venv\Scripts\deactivate.bat" (
    call venv\Scripts\deactivate.bat
)


