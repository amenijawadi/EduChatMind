"""
Convertit votre modèle XLM-RoBERTa entraîné au format compatible Rasa
IMPORTANT: Placez votre fichier model.safetensors dans ./kaggle_model/
"""
import torch
import json
import os
from transformers import XLMRobertaForSequenceClassification, XLMRobertaConfig

# Configuration
KAGGLE_MODEL_PATH = "./kaggle_model"  # Dossier contenant model.safetensors
OUTPUT_PATH = "./models"
NUM_LABELS = 28

# Les 28 émotions de votre modèle (ordre CRUCIAL - doit correspondre à l'entraînement)
EMOTION_LABELS = [
    'admiration', 'amusement', 'anger', 'annoyance', 'approval',
    'caring', 'confusion', 'curiosity', 'desire', 'disappointment',
    'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
    'gratitude', 'grief', 'joy', 'love', 'nervousness',
    'neutral', 'optimism', 'pride', 'realization', 'relief',
    'remorse', 'sadness', 'surprise'
]

def convert_model():
    """Convertit le modèle Kaggle au format utilisable par Rasa"""
    
    print("="*80)
    print("🔄 CONVERSION DU MODÈLE XLM-RoBERTa (28 ÉMOTIONS)")
    print("="*80)
    
    # Vérifier que le modèle source existe
    safetensors_path = os.path.join(KAGGLE_MODEL_PATH, "model.safetensors")
    if not os.path.exists(safetensors_path):
        print(f"❌ ERREUR: Fichier non trouvé: {safetensors_path}")
        print(f"   Veuillez placer model.safetensors de Kaggle dans {KAGGLE_MODEL_PATH}/")
        return False
    
    print(f"✅ Modèle source trouvé: {safetensors_path}")
    
    # Créer le dossier de sortie
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Charger le modèle depuis safetensors
    print("\n📥 Chargement du modèle...")
    try:
        model = XLMRobertaForSequenceClassification.from_pretrained(
            KAGGLE_MODEL_PATH,
            num_labels=NUM_LABELS,
            problem_type="single_label_classification"
        )
        print("✅ Modèle chargé avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return False
    
    # Sauvegarder au format PyTorch (.pt)
    print("\n💾 Conversion au format PyTorch (.pt)...")
    model_dict = {
        'model_state_dict': model.state_dict(),
        'num_labels': NUM_LABELS,
        'model_type': 'xlm-roberta-base',
        'emotion_labels': EMOTION_LABELS
    }
    
    torch.save(model_dict, os.path.join(OUTPUT_PATH, "model.pt"))
    print("✅ model.pt créé!")
    
    # Créer metadata.json
    print("\n📝 Création de metadata.json...")
    metadata = {
        "model_name": "xlm-roberta-base",
        "num_labels": NUM_LABELS,
        "emotion_labels": EMOTION_LABELS,
        "threshold": 0.5,  # Ajuster si nécessaire
        "max_length": 64,
        "problem_type": "single_label_classification",
        "training_info": {
            "best_epoch": 17,
            "val_f1_macro": 0.7956,
            "test_f1_macro": 0.7953
        }
    }
    
    with open(os.path.join(OUTPUT_PATH, "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)
    print("✅ metadata.json créé!")
    
    # Résumé
    print("\n" + "="*80)
    print("✅ CONVERSION RÉUSSIE!")
    print("="*80)
    print(f"\n📁 Fichiers créés dans {OUTPUT_PATH}/:")
    for f in os.listdir(OUTPUT_PATH):
        file_path = os.path.join(OUTPUT_PATH, f)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {f} ({size:,} bytes)")
    
    print(f"\n🎯 Émotions supportées: {len(EMOTION_LABELS)}")
    print(f"📊 Meilleur F1 (test): 0.7953")
    print(f"\n⚠️  PROCHAINE ÉTAPE: Exécutez tokenizer.py pour télécharger le tokenizer!")
    
    return True

if __name__ == "__main__":
    success = convert_model()
    if success:
        print("\n🎉 Prêt à être utilisé avec Rasa!")
    else:
        print("\n❌ La conversion a échoué. Vérifiez les erreurs ci-dessus.")