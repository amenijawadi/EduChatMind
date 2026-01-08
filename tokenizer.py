"""
Télécharge et sauvegarde le tokenizer XLM-RoBERTa
Compatible avec votre modèle entraîné
"""
from transformers import XLMRobertaTokenizerFast
import os

model_path = "./models"

print("🔄 Downloading xlm-roberta-base tokenizer...")
tokenizer = XLMRobertaTokenizerFast.from_pretrained('xlm-roberta-base')

# Créer le dossier si nécessaire
os.makedirs(model_path, exist_ok=True)

print(f"💾 Saving to {model_path}...")
tokenizer.save_pretrained(model_path)

print("✅ Tokenizer saved successfully!")

# Vérifier
files = os.listdir(model_path)
print(f"\n📁 Files in {model_path}:")
for f in sorted(files):
    file_path = os.path.join(model_path, f)
    if os.path.isfile(file_path):
        size = os.path.getsize(file_path)
        print(f"  - {f} ({size:,} bytes)")

print("\n🎉 Ready to use with XLM-RoBERTa!")
print(f"📊 Vocab size: {len(tokenizer)}")