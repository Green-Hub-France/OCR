# Base image with Debian and Python
FROM python:3.12-slim

# Installer les dépendances système pour Tesseract et autres bibliothèques
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tesseract-ocr \
      libtesseract-dev \
      libleptonica-dev \
      pkg-config \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port Streamlit
EXPOSE 8501

# Variable d'environnement pour Tesseract
ENV TESSDATA_PREFIX=/usr/share/tessdata

# Commande de démarrage
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
