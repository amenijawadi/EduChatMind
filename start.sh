#!/bin/bash

# Print environment info
echo "Starting application..."
echo "Current directory: $(pwd)"
echo "Models available: $(ls models/)"

# Télécharger le modèle SpaCy si pas déjà présent (au 1er démarrage)
echo "Checking SpaCy models..."
python -m spacy download en_core_web_md 2>/dev/null || echo "SpaCy model already downloaded"

# Start the Rasa action server
echo "Starting Action Server on port 5055..."
rasa run actions --port 5055 &

# Start the Rasa server
echo "Starting Rasa Server on port ${PORT:-5005}..."
exec rasa run --enable-api --cors "*" --port ${PORT:-5005} --debug --model models/
