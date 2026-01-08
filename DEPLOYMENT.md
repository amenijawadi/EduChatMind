# 🚀 Guide de Déploiement - EduChatMind

Ce guide vous accompagne étape par étape pour déployer votre projet EduChatMind sur le cloud.

## 📁 Fichiers Créés

J'ai préparé tous les fichiers nécessaires pour le déploiement :

### ✅ Configuration
- ✅ `requirements.txt` - Dépendances Python
- ✅ `packages.txt` - Dépendances système
- ✅ `.gitignore` - Fichiers à exclure de Git
- ✅ `.env.example` - Template des variables d'environnement
- ✅ `.streamlit/config.toml` - Configuration Streamlit

### ✅ Scripts de Déploiement
- ✅ `download_model.py` - Télécharge le modèle depuis Hugging Face
- ✅ `upload_model_to_hf.py` - Upload le modèle vers Hugging Face
- ✅ `Dockerfile` - Pour déployer Rasa
- ✅ `railway.json` - Configuration Railway.app

## 🎯 Prochaines Étapes

### 1️⃣ Préparer le Projet (10 min)

**Important** : Avant de commencer, vous devez d'abord modifier certains fichiers pour personnaliser votre déploiement.

#### A. Obtenir un Token Hugging Face
1. Allez sur https://huggingface.co/settings/tokens
2. Créez un nouveau token avec permission **write**
3. Copiez le token (commence par `hf_...`)

#### B. Créer un Repository Hugging Face
1. Allez sur https://huggingface.co/new
2. Créez un nouveau modèle nommé `educhatmind-model`
3. Notez votre username HF

#### C. Configurer `upload_model_to_hf.py`
Éditez le fichier et remplacez :
```python
repo_id = "VOTRE_USERNAME/educhatmind-model"  # Ex: "john-doe/educhatmind-model"
token = "hf_VOTRE_TOKEN"  # Votre token HF
```

#### D. Upload le Modèle (⏱️ 10-30 min selon connexion)
```bash
python upload_model_to_hf.py
```

### 2️⃣ Configurer MongoDB Atlas (15 min)

1. Créez un compte sur https://mongodb.com/atlas
2. Créez un cluster gratuit (M0)
3. Créez un utilisateur avec mot de passe
4. Autorisez l'accès depuis `0.0.0.0/0`
5. Copiez la **Connection String**

### 3️⃣ Pousser sur GitHub (5 min)

```bash
git init
git add .
git commit -m "Ready for deployment"
# Créez un repo sur GitHub puis :
git remote add origin https://github.com/VOTRE_USERNAME/educhatmind.git
git push -u origin main
```

### 4️⃣ Déployer sur Streamlit Cloud (10 min)

1. Allez sur https://streamlit.io/cloud
2. Connectez-vous avec GitHub
3. **New app** → Sélectionnez votre repo
4. Main file: `web_app.py`
5. **Advanced settings** → **Secrets** :

```toml
MONGODB_URI = "mongodb+srv://user:password@cluster.mongodb.net/"
MONGODB_DB_NAME = "rasa"
HF_TOKEN = "hf_VOTRE_TOKEN"
HF_REPO_ID = "votre-username/educhatmind-model"
RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"
DEMO_MODE = "true"
```

6. Cliquez **Deploy**

### 5️⃣ (Optionnel) Déployer Rasa

Si vous voulez le chatbot fonctionnel :

#### Railway.app
1. Allez sur https://railway.app
2. **New Project** → **Deploy from GitHub**
3. Sélectionnez votre repo
4. Railway détectera automatiquement le `Dockerfile`
5. Copiez l'URL générée
6. Mettez à jour le secret Streamlit :
```toml
RASA_API_URL = "https://votre-app.railway.app/webhooks/rest/webhook"
DEMO_MODE = "false"
```

## 📚 Voir le Guide Complet

Pour plus de détails, consultez le [Guide de Déploiement Complet](file:///C:/Users/Lenovo/.gemini/antigravity/brain/4ae774c1-5b20-4e67-9350-fc842b52dcf6/guide_deployment.md) qui contient :

- 📖 Explications détaillées de chaque étape
- 🔧 Solutions de dépannage
- 💡 Optimisations et bonnes pratiques
- 📊 Architecture complète
- 💰 Estimation des coûts

## ⚠️ Points Importants

> [!IMPORTANT]
> **Modèle de 1.1 GB** : Le modèle est trop volumineux pour Streamlit Cloud. Il DOIT être hébergé sur Hugging Face.

> [!WARNING]
> **MongoDB** : Ne pas utiliser `localhost` en production. Utilisez MongoDB Atlas.

> [!TIP]
> **Mode Démo** : Vous pouvez déployer l'interface Streamlit sans Rasa en activant `DEMO_MODE = "true"` et déployer Rasa plus tard.

## 🆘 Besoin d'Aide ?

- 📖 [Guide Complet](file:///C:/Users/Lenovo/.gemini/antigravity/brain/4ae774c1-5b20-4e67-9350-fc842b52dcf6/guide_deployment.md)
- 🌐 [Streamlit Docs](https://docs.streamlit.io/streamlit-community-cloud)
- 🤗 [Hugging Face Docs](https://huggingface.co/docs/hub)
- 🍃 [MongoDB Atlas Docs](https://www.mongodb.com/docs/atlas/)

**Bonne chance avec votre déploiement ! 🚀**
