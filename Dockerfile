FROM rasa/rasa:3.6.0-full

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Installer les dépendances Python supplémentaires si nécessaire
# RUN pip install -r requirements-rasa.txt

# Télécharger le modèle SpaCy
RUN python -m spacy download en_core_web_md

# Entraîner le modèle Rasa
RUN rasa train

# Exposer le port
EXPOSE 5005

# Commande de démarrage
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--port", "5005", "--debug"]
