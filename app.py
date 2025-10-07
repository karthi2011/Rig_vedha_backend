from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import os
import gc
import json
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)
PDF_PATH = os.path.join(BASE_DIR, "rigvedha.pdf")
RESULTS_FILE = os.path.join(BASE_DIR, "data", "results.json")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "w") as f:
        json.dump([], f)

@app.route("/api/pdf")
def serve_pdf():
    return send_file(PDF_PATH, "rigvedha.pdf")

@app.route("/api/quiz/generate", methods=["POST"])
def generate_quiz():
    payload = request.json or {}
    count = int(payload.get("count", 5))

    if not GEMINI_KEY:
        return jsonify({"error": "Gemini API key not set"}), 400

    try:
        # Use direct Gemini API instead of LangChain
        model = genai.GenerativeModel('gemini-1.5-flash')  # Lighter model
        
        prompt = f"""
        Generate {count} different multiple choice questions about Rig Vedha.
        Each question must have 4 options and specify the correct answer index (0-3).
        Return the result as pure JSON array with objects having fields: q, options, answer_index.
        
        Example format:
        [
            {{
                "q": "What is Rig Vedha?",
                "options": ["Ancient text", "Modern book", "Movie", "Song"],
                "answer_index": 0
            }}
        ]
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip().strip("`").strip("json").strip()
        
        quiz = json.loads(response_text)
        print(quiz)
        
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Fallback questions
        quiz = [
            {"q": "What is Rig Vedha?", "options": ["Ancient Hindu scripture", "Modern book", "Movie", "Song"], "answer_index": 0},
            {"q": "How many mandalas are in Rig Vedha?", "options": ["10", "7", "5", "12"], "answer_index": 0},
            {"q": "Which language is Rig Vedha written in?", "options": ["Sanskrit", "Hindi", "Tamil", "English"], "answer_index": 0}
        ][:count]
    
    finally:
        gc.collect()
    
    return jsonify(quiz)

@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    payload = request.json or {}
    name = payload.get("name", "Anonymous")
    answers = payload.get("answers", [])
    questions = payload.get("questions", [])

    score = 0
    for i, q in enumerate(questions):
        correct = q.get("answer_index")
        if i < len(answers) and answers[i] == correct:
            score += 1

    result = {"name": name, "score": score, "total": len(questions)}

    with open(RESULTS_FILE, "r+") as f:
        data = json.load(f)
        data.append(result)
        f.seek(0)
        json.dump(data, f, indent=2)

    return jsonify(result)

@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.json or {}
    message = payload.get("message", "")
    
    if not GEMINI_KEY:
        return jsonify({"reply": "Gemini API key not found."}), 400
    
    try:
        # Use direct Gemini API instead of LangChain
        model = genai.GenerativeModel('gemini-1.0-pro')  # Lighter model
        
        prompt = f"You are an expert on Rig Vedha. Answer this question clearly and concisely: {message}. Only answer Rig Vedha related questions."
        
        response = model.generate_content(prompt)
        reply = response.text
        
    except Exception as e:
        print(f"Chat error: {e}")
        reply = "I'm sorry, I couldn't process your question about Rig Vedha at the moment."
    
    finally:
        gc.collect()
    
    return jsonify({"reply": reply})

@app.route('/')
def home():
    return {"status": "OK", "message": "Rig Vedha Backend is running"}

if __name__ == "__main__":
    app.run(port=5000, debug=True)