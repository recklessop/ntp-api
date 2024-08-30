#!/bin/bash

# Navigate to the directory containing your FastAPI application
cd /home/justin/api

# Activate the virtual environment (if you're using one)
source /home/justin/api/env/bin/activate

# Check if the process is already running
if pgrep -f "uvicorn main:app" > /dev/null
then
    echo "FastAPI is already running"
else
    # Run the FastAPI application with uvicorn without auto-reload
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
    echo "FastAPI started"
fi
