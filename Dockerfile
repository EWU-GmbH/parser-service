# Wir nutzen ein schlankes Python Image als Basis
FROM python:3.11-slim

# System-Tools installieren (Wichtig für PDF und OCR)
# Wir installieren explizit das deutsche Sprachpaket (tesseract-ocr-deu)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis im Container setzen
WORKDIR /app

# Python-Bibliotheken installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NLTK Daten herunterladen (wird von Unstructured benötigt)
RUN python -m nltk.downloader punkt averaged_perceptron_tagger

# Den Rest des Codes kopieren
COPY . .

# Startbefehl: Wir nutzen Gunicorn als stabilen Webserver
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "main:app"]
