from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import google.generativeai as genai
from rag_utils import get_context_from_gcs
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "max_output_tokens": 200,
}

model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)

BUCKET_NAME = "sejarah"
FILE_NAME = "knowledge.txt"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question")
    karakter = data.get("karakter")

    prompt = get_context_from_gcs(BUCKET_NAME, FILE_NAME, karakter, question)
    response = model.generate_content(prompt)

    return jsonify({
        "karakter": karakter,
        "response": response.text
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)