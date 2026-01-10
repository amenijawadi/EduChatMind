from huggingface_hub import HfApi, create_repo
import os

# Configuration - REMPLACEZ AVEC VOS VALEURS
# IMPORTANT: ne jamais mettre le token en dur dans le code.
# On lit repo_id et token depuis les variables d'environnement pour éviter les fuites.
repo_id = os.getenv("HF_REPO_ID", "amaniJaouadi/educhatmind-model")  # Ex: "john-doe/educhatmind-model"
token = os.getenv("HF_TOKEN")  # Ou utilisez: huggingface-cli login

# Créer le repo (si pas déjà fait)
try:
    create_repo(repo_id, token=token, exist_ok=True, private=False)
    print(f"✅ Repository {repo_id} créé/vérifié")
except Exception as e:
    print(f"ℹ️  Repo existe déjà ou erreur: {e}")

# Upload le modèle
api = HfApi()

files_to_upload = [
    "models/model.pt",
    "models/config.json",
    "models/metadata.json",
    "models/sentencepiece.bpe.model",
    "models/tokenizer.json",
    "models/tokenizer_config.json",
    "models/special_tokens_map.json"
]

print(f"\n📤 Uploading files to Hugging Face...")
print(f"⚠️  This may take 10-30 minutes for the 1.1GB model\n")

for file_path in files_to_upload:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"📤 Uploading {file_path} ({file_size:.1f} MB)...")
        
        try:
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=os.path.basename(file_path),
                repo_id=repo_id,
                token=token
            )
            print(f"✅ {file_path} uploaded!")
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
    else:
        print(f"⚠️  File not found: {file_path}")

print(f"\n🎉 Upload complete!")
print(f"🔗 View your model at: https://huggingface.co/{repo_id}")
