#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: ${SCRIPT_DIR}"

# Kill any existing process on port 8061
echo "Killing any existing processes on port 8061..."
lsof -ti:8061 | xargs kill -9 2>/dev/null

# Activate virtual environment
echo "Activating virtual environment..."
source "${SCRIPT_DIR}/venv/bin/activate"

# Start the port killer in the background
echo "Starting port killer..."
"${SCRIPT_DIR}/port_killer.sh" &

# Start the dashboard
echo "Starting dashboard..."
cd "${SCRIPT_DIR}/src"
echo "Changed to directory: $(pwd)"

# Add browser opening
echo "Starting Python app and opening browser..."
python app.py &
sleep 3
open "http://127.0.0.1:8061"

# Wait for the Python process
wait