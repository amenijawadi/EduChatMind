#!/usr/bin/env python3
"""
Script pour entraîner le modèle Rasa
Exécutez ceci localement: python train_model.py
"""

import subprocess
import sys
import os

def train_rasa_model():
    """Entraîner le modèle Rasa avec les données actuelles"""
    
    print("=" * 60)
    print("Entraînement du modèle Rasa...")
    print("=" * 60)
    
    # Vérifier que les fichiers de données existent
    data_dir = "data"
    required_files = ["nlu.yml", "stories.yml", "rules.yml"]
    
    for file in required_files:
        filepath = os.path.join(data_dir, file)
        if not os.path.exists(filepath):
            print(f"⚠️  AVERTISSEMENT: {filepath} n'existe pas!")
            print(f"   Les données d'entraînement doivent être dans: data/nlu.yml, data/stories.yml, data/rules.yml")
    
    # Exécuter rasa train
    try:
        result = subprocess.run(
            ["rasa", "train", "--domain", "domain.yml", "--data", "data/", "--out", "models/"],
            check=True
        )
        print("\n" + "=" * 60)
        print("✅ Modèle entraîné avec succès!")
        print("=" * 60)
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ Erreur lors de l'entraînement:")
        print(str(e))
        print("=" * 60)
        return 1
    except FileNotFoundError:
        print("❌ Erreur: 'rasa' command not found. Install Rasa first:")
        print("   pip install rasa")
        return 1

if __name__ == "__main__":
    exit_code = train_rasa_model()
    sys.exit(exit_code)
