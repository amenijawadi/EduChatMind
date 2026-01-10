#!/bin/bash

# Print environment info
echo "Starting application..."
echo "Current directory: $(pwd)"
echo "Models available: $(ls -la models/ | head -20)"

# Start the Rasa action server
echo "Starting Action Server on port 5055..."
rasa run actions --port 5055 &

# Start the Rasa server with model
echo "Starting Rasa Server on port ${PORT:-10000}..."
if [ -f models/model.tar.gz ]; then
    echo "Found trained model, loading..."
    exec rasa run \
      --enable-api \
      --cors "*" \
      --credentials credentials.yml \
      --port ${PORT:-10000} \
      --debug \
      --model models/model.tar.gz
else
    echo "⚠️  No trained model found. Running in demo mode (responses may be limited)"
    exec rasa run \
      --enable-api \
      --cors "*" \
      --credentials credentials.yml \
      --port ${PORT:-10000} \
      --debug
fi
