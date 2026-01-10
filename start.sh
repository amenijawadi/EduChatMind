#!/bin/bash

# Print environment info
echo "Starting application..."
echo "Current directory: $(pwd)"
echo "Models available: $(ls -la models/ | head -20)"

# Télécharger le modèle SpaCy si pas déjà présent (au 1er démarrage)
echo "Checking SpaCy models..."
python -m spacy download en_core_web_md 2>/dev/null || echo "SpaCy model already downloaded"

# Start the Rasa action server
echo "Starting Action Server on port 5055..."
rasa run actions --port 5055 &

# Start the Rasa server (avec mode de fallback si pas de modèle)
echo "Starting Rasa Server on port ${PORT:-5005}..."
if [ -f models/*.tar.gz ] || [ -d models/components ]; then
    echo "Found trained model, loading..."
    exec rasa run --enable-api --cors "*" --port ${PORT:-5005} --debug --model models/
else
    echo "⚠️  No trained model found. Running in demo mode (responses may be limited)"
    exec rasa run --enable-api --cors "*" --port ${PORT:-5005} --debug
fi
