from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv


# --- Load environment variables ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")


# --- LangChain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain



app = Flask(__name__)
CORS(app)#, resources={r"/*": {"origins": "*"}})

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
# Serve the PDF file for the frontend to embed
    return send_file(PDF_PATH, "rigvedha.pdf")



@app.route("/api/quiz/generate", methods=["POST"])
def generate_quiz():
    payload = request.json or {}
    count = int(payload.get("count", 5))

    if not GEMINI_KEY:
        return jsonify({"error": "Gemini API key not set"}), 400

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=GEMINI_KEY)

    prompt = PromptTemplate.from_template(
        "Generate {count} different multiple choice questions about Rig Vedha. "
        "Each question must have 4 options and specify the correct answer index (0-3). "
        "Return the result as pure JSON array with objects having fields: q, options with words, answer_index."
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(count=count)
    print(type(response))
    #print(response)
    response=response.strip("`json").rstrip('```')
    print(response)
    try:
        quiz = json.loads(response.strip())
        print(quiz)
    except Exception:
        quiz = [
            {"q": "What is Rig Vedha?", "options": ["A", "B", "C", "D"], "answer_index": 0}
        ] * count

    return jsonify(quiz)




@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    # Expect: {"name": "User", "answers": [0,2,1,3,0], "questions": [...]}
    payload = request.json or {}
    name = payload.get("name", "Anonymous")
    answers = payload.get("answers", [])
    questions = payload.get("questions", [])

    print(name)
    print("Answer",answers)
    print(questions)
    score = 0
    for i, q in enumerate(questions):
        correct = q.get("answer_index")
        if i < len(answers) and answers[i] == correct:
         score += 1


    result = {"name": name, "score": score, "total": len(questions)}

    print("RESTULTs",result)
    # Save to file
    with open(RESULTS_FILE, "r+") as f:
        data = json.load(f)
        data.append(result)
        f.seek(0)
        json.dump(data, f, indent=2)


    return jsonify(result)



@app.route("/api/chat", methods=["POST"])
def chat():
    # Expect: {"message": "question about Rig Vedha"}
    payload = request.json or {}
    message = payload.get("message", "")
    if not GEMINI_KEY:
        return jsonify({"reply": "Gemini API key not found."}), 400

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=GEMINI_KEY)
    prompt = PromptTemplate.from_template("You are an expert on Rig Vedha. Answer clearly: {question}. Only answer for Rig vedha related question")
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(question=message)

    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(port=5000, debug=True)