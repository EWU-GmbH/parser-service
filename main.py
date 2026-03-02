import os
from flask import Flask, request, jsonify
# Wir nutzen 'partition' statt 'partition_pdf', damit das Tool ALLES lesen kann (PDF, Docx, Bilder)
from unstructured.partition.auto import partition
from mistralai import Mistral

app = Flask(__name__)

# 1. KONFIGURATION LADEN
api_key = os.environ.get("MISTRAL_API_KEY")
service_secret = os.environ.get("SERVICE_SECRET")  # Dein selbstgewähltes Passwort

client = Mistral(api_key=api_key) if api_key else None

@app.route('/parse', methods=['POST'])
def parse_document():
    # 2. SICHERHEITS-CHECK (API Key Prüfung)
    # Wenn du in Coolify ein SERVICE_SECRET gesetzt hast, wird es hier geprüft.
    if service_secret:
        auth_header = request.headers.get('X-API-Key')
        if auth_header != service_secret:
            return jsonify({"error": "Unauthorized: Falscher API Key"}), 401

    # Standard-Checks
    if not client: return jsonify({"error": "MISTRAL_API_KEY nicht gesetzt"}), 500
    if 'file' not in request.files: return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    # 3. DYNAMISCHE ANWEISUNG
    # Hier holen wir uns deine Anweisung ab (z.B. "Extrahiere CV Daten").
    # Falls du nichts mitschickst, nehmen wir diesen Standard:
    default_instruction = """
    Analysiere dieses Dokument. Extrahiere die wichtigsten Stammdaten und den Inhalt 
    als strukturiertes JSON.
    """
    user_instruction = request.form.get('instruction', default_instruction)

    # Dateihandling (Originalnamen nutzen für bessere Typerkennung)
    file = request.files['file']
    filename = file.filename if file.filename else "doc"
    temp_path = os.path.join("/tmp", filename)
    
    try:
        file.save(temp_path)
        
        # 4. UNIVERSAL PARSING
        # "hi_res" aktiviert OCR für Bilder/PDFs.
        # "partition" entscheidet automatisch, ob es PDF, Word oder Excel ist.
        elements = partition(
            filename=temp_path, 
            strategy="hi_res",           
            infer_table_structure=True,  # Wichtig für Tabellen in Rechnungen/CVs
            languages=["deu", "eng"]     # Deutsch & Englisch
        )
        
        text_content = "\n\n".join([str(el) for el in elements])
        
        # 5. KI-ANALYSE
        prompt = f"""
        {user_instruction}
        
        Antworte bitte ausschließlich mit dem Ergebnis (z.B. reines JSON), ohne Einleitungstext.
        
        Dokument-Inhalt:
        {text_content[:25000]}
        """

        chat_response = client.chat.complete(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": prompt}]
            # Wir entfernen hier "json_object", damit du auch normale Text-Zusammenfassungen anfordern kannst.
            # Wenn du JSON willst, schreib es einfach in deine "instruction".
        )
        
        # Aufräumen
        if os.path.exists(temp_path): os.remove(temp_path)
        
        return chat_response.choices[0].message.content, 200

    except Exception as e:
        # Aufräumen im Fehlerfall
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
