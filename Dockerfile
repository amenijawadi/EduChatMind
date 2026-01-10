FROM rasa/rasa:3.6.0

# Copier les fichiers Rasa
WORKDIR /app
COPY . /app

# Switch to root to install dependencies and fix permissions
USER root

# Installer les dépendances pour l'action server (pipeline légère, sans SpaCy)
RUN pip install --no-cache-dir --no-warn-script-location -r requirements-rasa.txt \
    && pip install --force-reinstall --no-cache-dir filelock \
    && rm -rf /root/.cache/pip /tmp/* \
    && find /opt/venv -type f -name "*.pyc" -delete \
    && find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /root/.cache

# Donner les permissions au script de démarrage
RUN chmod +x /app/start.sh

# Revenir à l'utilisateur Rasa par défaut
USER 1001

# Exposer le port du serveur Rasa principal (Render fournit PORT=10000)
EXPOSE 10000

# IMPORTANT: Override ENTRYPOINT to run start.sh instead of 'rasa' command
ENTRYPOINT []

# Commande de démarrage
CMD ["/app/start.sh"]
