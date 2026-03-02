import os
from flask import Flask, request, jsonify
from unstructured.partition.pdf import partition_pdf
from mistralai import Mistral

app = Flask(__name__)

api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None

@app.route('/parse-cv', methods=['POST'])
def parse_cv():
    if not client: return jsonify({"error": "No API Key"}), 500
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
        
    temp_path = "/tmp/temp_cv.pdf"
    try:
        file = request.files['file']
        file.save(temp_path)
        
        # HIER IST DER UNTERSCHIED:
        # "hi_res" nutzt KI, um das Layout zu verstehen (Spalten, Header, etc.)
        # Das ist langsamer (10-30 Sek), aber extrem genau.
        elements = partition_pdf(
            temp_path, 
            strategy="hi_res",           
            infer_table_structure=True,  # Tabellen in CVs verstehen
            languages=["deu", "eng"]     # Deutsche OCR aktivieren
        )
        
        # Text intelligent zusammenbauen
        text_content = "\n\n".join([str(el) for el in elements])
        
        # Analyse durch Mistral
        prompt = f"""
        Analysiere diesen Lebenslauf. Extrahiere als JSON:
        - vorname, nachname, email, telefon
        - skills (als Array)
        - letzte_position (Titel, Firma, Zeitraum)
        - ausbildung (höchster Abschluss)
        
        Text:
        {text_content[:25000]}
        """

        chat_response = client.chat.complete(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        if os.path.exists(temp_path): os.remove(temp_path)
        return chat_response.choices[0].message.content, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
