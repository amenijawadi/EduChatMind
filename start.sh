#!/bin/bash

# Start the Rasa action server
rasa run actions --port 5055 &

# Start the Rasa server
rasa run --enable-api --cors "*" --port ${PORT:-5005} --debug
