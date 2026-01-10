#!/bin/bash

# Give other services time to start (matching example pattern)
sleep 3

# Start the application using main.py as requested
python3 main.py

# Keep container alive if the process exits
while true; do sleep 1000; done
