# VRPTW Streamlit App Documentation

## Files Needed for Deployment

The following files are required for the Streamlit Cloud deployment:

### Core Files
- `vrptw_app.py` - Main Streamlit application
- `vrptw_solver.py` - VRPTW solver module
- `locations.csv` - Sample location data (198 locations in Rochester, NY)
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

### Optional Files
- `README_VRPTW.md` - Detailed solver documentation
- `run_app.sh` / `run_app.bat` - Local run scripts (not used on Streamlit Cloud)

## Deploying to Streamlit Cloud

### Step 1: Push to GitHub

1. Initialize git repository (if not already done):
```bash
git init
git add .
git commit -m "Initial commit: VRPTW Solver app"
```

2. Create a new repository on GitHub (e.g., `vrptw-solver`)

3. Push to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/vrptw-solver.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select:
   - **Repository**: YOUR_USERNAME/vrptw-solver
   - **Branch**: main
   - **Main file path**: vrptw_app.py
5. Click "Deploy"

### Step 3: Update README Badge

After deployment, update the badge URL in README.md:
```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-NAME.streamlit.app)
```

## Local Development

### Setup
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run
```bash
streamlit run vrptw_app.py
```

Or use the provided scripts:
- Windows: `run_app.bat`
- Linux/Mac: `./run_app.sh`

## Configuration

### Custom Port (Local)
```bash
streamlit run vrptw_app.py --server.port 8502
```

### Debug Mode
```bash
streamlit run vrptw_app.py --logger.level=debug
```

## Troubleshooting

### Import Errors on Streamlit Cloud
- Ensure all dependencies are in `requirements.txt`
- Check package versions are compatible
- Streamlit Cloud uses Python 3.9+ by default

### Memory Issues
- Limit the number of locations processed
- Reduce max solving time
- The app uses efficient algorithms but large problems (>500 locations) may timeout

### File Upload Issues
- CSV must have required columns: name, address, latitude, longitude
- First row is treated as depot
- Coordinates must be valid decimal degrees

## App Settings

### Sidebar Width
Controlled by custom CSS in `vrptw_app.py` (currently 400px)

### File Upload Limit
Default: 200MB (Streamlit Cloud default)

### Session State
The app uses `st.session_state` to persist:
- Uploaded data
- Parameter values
- Solution results
- View state (Locations/Solution toggle)

## Performance Notes

- **Small problems** (20 locations): ~5-30 seconds
- **Medium problems** (50 locations): ~30-90 seconds
- **Large problems** (100+ locations): 1-5 minutes (may require longer max_runtime)

## Security

- No API keys are required
- No user data is stored permanently
- All computations run in the user's session
- Session data is cleared when the browser tab closes
