FROM rasa/rasa:3.6.0

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Switch to root to install dependencies and fix permissions
USER root

# Installer les dépendances pour l'action server (Torch/Transformers)
# Utilisation de --extra-index-url pour installer les versions CPU de torch pour économiser de la RAM et de l'espace disque
RUN pip install --no-cache-dir --no-warn-script-location \
    filelock \
    spacy \
    torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --no-warn-script-location -r requirements-rasa.txt && \
    rm -rf /root/.cache/pip /tmp/* && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /root/.cache

# Donner les permissions au script de démarrage
RUN chmod +x /app/start.sh

# Revenir à l'utilisateur Rasa par défaut
USER 1001

# Exposer le port
EXPOSE 5005

# IMPORTANT: Override ENTRYPOINT to run start.sh instead of 'rasa' command
ENTRYPOINT []

# Commande de démarrage
CMD ["/app/start.sh"]
