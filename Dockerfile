FROM rasa/rasa:3.6.0 AS builder

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Switch to root to install dependencies and fix permissions
USER root

# Installer les dépendances pour l'action server (Torch/Transformers)
# Utilisation de --extra-index-url pour installer les versions CPU de torch pour économiser de la RAM et de l'espace disque
RUN pip install --no-cache-dir --no-warn-script-location \
    spacy \
    torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --no-warn-script-location -r requirements-rasa.txt && \
    rm -rf /root/.cache/pip && \
    find /usr/local -name "*.pyc" -delete && \
    find /usr/local -name "__pycache__" -type d -delete && \
    find /usr/local -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Télécharger le modèle SpaCy (APRÈS installation de spacy)
RUN python -m spacy download en_core_web_md

# ============= STAGE 2: Runtime (allégé) =============
FROM rasa/rasa:3.6.0

WORKDIR /app

# Copier UNIQUEMENT les fichiers nécessaires du builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

USER root

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
