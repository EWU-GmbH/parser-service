FROM python:3.11-slim

# WICHTIG: Tesseract und System-Tools für die Bildverarbeitung
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libmagic1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Das Installieren dauert beim ersten Mal 3-5 Minuten (große Downloads!)
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader punkt averaged_perceptron_tagger

COPY . .

# Timeout hoch lassen (120s), da KI-Analyse Zeit kostet
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "main:app"]
