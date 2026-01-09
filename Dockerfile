FROM rasa/rasa:3.6.0-full

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Installer les dépendances Python supplémentaires si nécessaire
# RUN pip install -r requirements-rasa.txt

# Télécharger le modèle SpaCy
RUN python -m spacy download en_core_web_md

# Switch to root to fix permissions
USER root

# Donner les permissions au script de démarrage
RUN chmod +x /app/start.sh

# Entraîner le modèle Rasa (nécessite root pour écrire dans /app)
RUN rasa train

# Revenir à l'utilisateur Rasa par défaut
USER 1001

# Exposer le port
EXPOSE 5005

# Commande de démarrage
CMD ["/app/start.sh"]
