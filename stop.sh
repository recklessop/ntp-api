#!/bin/bash

# Check if the process is running
PID=$(pgrep -f "uvicorn main:app")

if [ -z "$PID" ]; then
    echo "FastAPI is not running"
else
    echo "Stopping FastAPI with PID $PID"
    kill $PID
    echo "FastAPI stopped"
fi
