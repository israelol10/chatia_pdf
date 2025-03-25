from flask import Flask, request, jsonify
import openai
import requests
import os

app = Flask(__name__)

# Configuración de Azure OpenAI desde variables de entorno
openai.api_type = "azure"
openai.api_base = "https://pruebai.openai.azure.com/"
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")

# Configuración de Azure Cognitive Search desde variables de entorno
azure_search_endpoint = "https://azuretrialpdf.search.windows.net"
azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
azure_search_index = "documento"

def search_pdf_content(prompt):
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_search_api_key
    }
    search_url = f"{azure_search_endpoint}/indexes/{azure_search_index}/docs/search?api-version=2021-04-30-Preview"
    
    search_payload = {
        "search": prompt,
        "select": "content",
        "top": 1
    }
    
    response = requests.post(search_url, headers=headers, json=search_payload)
    if response.status_code == 200:
        result = response.json()
        if 'value' in result and len(result['value']) > 0:
            return result['value'][0]['content']
    return None

@app.route('/search_pdf', methods=['POST'])
def search_pdf():
    user_query = request.json.get("query", "")
    if not user_query:
        return jsonify({"error": "Consulta vacía"}), 400

    pdf_content = search_pdf_content(user_query)
    if pdf_content:
        try:
            response = openai.ChatCompletion.create(
                deployment_id="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Usa solo la información proporcionada para responder la pregunta del usuario."},
                    {"role": "system", "content": f"Información extraída: {pdf_content}"},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500
            )
            answer = response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            answer = f"Error al procesar la solicitud: {e}"
    else:
        answer = "No se encontró información relevante en el índice de búsqueda."
    
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
