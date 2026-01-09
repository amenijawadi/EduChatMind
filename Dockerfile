FROM rasa/rasa:3.6.0-full

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Télécharger le modèle SpaCy
RUN python -m spacy download en_core_web_md

# Switch to root to install dependencies and fix permissions
USER root

# Installer les dépendances pour l'action server (Torch/Transformers)
RUN pip install --no-cache-dir -r requirements-rasa.txt

# Donner les permissions au script de démarrage
RUN chmod +x /app/start.sh

# Entraîner le modèle Rasa (nécessite root pour écrire dans /app)
RUN rasa train

# Revenir à l'utilisateur Rasa par défaut
USER 1001

# Exposer le port
EXPOSE 5005

# IMPORTANT: Override ENTRYPOINT to run start.sh instead of 'rasa' command
ENTRYPOINT []

# Commande de démarrage
CMD ["/app/start.sh"]
