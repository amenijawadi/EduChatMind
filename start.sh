#!/bin/bash

# Print environment info
echo "Starting application..."
echo "Current directory: $(pwd)"
echo "Models available: $(ls models/)"

# Start the Rasa action server
echo "Starting Action Server on port 5055..."
rasa run actions --port 5055 &

# Start the Rasa server
echo "Starting Rasa Server on port ${PORT:-5005}..."
exec rasa run --enable-api --cors "*" --port ${PORT:-5005} --debug --model models/
