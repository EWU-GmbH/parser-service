import os
from flask import Flask, request, jsonify
from unstructured.partition.pdf import partition_pdf
from mistralai import Mistral

app = Flask(__name__)

# API Key sicher aus den Coolify-Umgebungsvariablen laden
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None

@app.route('/parse-cv', methods=['POST'])
def parse_cv():
    # Sicherheitscheck: Ist ein API Key da?
    if not client:
        return jsonify({"error": "MISTRAL_API_KEY not set"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    try:
        file = request.files['file']
        temp_path = "/tmp/temp_cv.pdf"
        file.save(temp_path)
        
        # 1. Parsing: PDF in Text umwandeln (Hier arbeitet dein Server kurz)
        # strategy="hi_res" nutzt OCR, falls nötig.
        elements = partition_pdf(
            temp_path, 
            strategy="hi_res", 
            languages=["deu", "eng"]
        )
        text_content = "\n\n".join([str(el) for el in elements])
        
        # 2. KI-Analyse: Text an Mistral (EU) senden
        # Wir kürzen den Text sicherheitshalber auf 25.000 Zeichen, damit das Limit nicht gesprengt wird
        prompt = f"""
        Du bist ein HR-Daten-Experte. Extrahiere die folgenden Daten aus dem Lebenslauf und gib sie NUR als JSON zurück.
        Format: {{ "vorname": "", "nachname": "", "email": "", "skills": ["skill1", "skill2"], "letzte_position": "" }}
        
        Lebenslauf Text:
        {text_content[:25000]}
        """

        chat_response = client.chat.complete(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Aufräumen
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # JSON Ergebnis zurückgeben
        return chat_response.choices[0].message.content, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        # Aufräumen im Fehlerfall
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
