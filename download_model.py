import os
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

# Charge automatiquement les variables définies dans un fichier .env (en local)
load_dotenv()

def download_model_from_hf():
    """Télécharge le modèle depuis Hugging Face si absent"""
    
    model_path = "models/model.pt"
    
    # Si le modèle existe déjà, ne pas re-télécharger
    if os.path.exists(model_path):
        print(f"✅ Model already exists at {model_path}")
        return model_path
    
    # Paramètres HF
    repo_id = os.getenv("HF_REPO_ID", "VOTRE_USERNAME/educhatmind-model")
    token = os.getenv("HF_TOKEN", None)
    
    print(f"📥 Downloading model from {repo_id}...")
    
    try:
        # Créer le dossier models s'il n'existe pas
        os.makedirs("models", exist_ok=True)
        
        # Télécharger le modèle principal
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename="model.pt",
            token=token,
            cache_dir="models",
            local_dir="models",
            local_dir_use_symlinks=False
        )
        
        print(f"✅ Model downloaded to {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

# Télécharger au démarrage
if __name__ == "__main__":
    download_model_from_hf()
