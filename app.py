import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat_history = []
financial_data = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_financial_data", methods=["POST"])
def set_financial_data():
    global financial_data
    financial_data = request.json
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history, financial_data

    user_message = request.json.get("message")

    chat_history.append({"role": "user", "content": user_message})

    system_prompt = f"""
        You are a financial assistant.

        User financial data (all amounts are in monetary terms, e.g. dollars and not in percentages):
        {json.dumps(financial_data)}

        Notes:
        - Expenses are dynamic categories (user-defined)
        - Do NOT assume fixed categories

        Instructions:
        1. Chat Response:
        - Use a PROFESSIONAL financial advisor tone
        - Use proper capitalization
        - Use proper grammar and punctuation

        IMPORTANT:
        - If not enough info is collected, you may prompt for more information, but do not badger the user for too many details. Only ask for what is necessary to provide a recommendation.
        - If you prompt for more information, SKIP EVERYTHING BELOW, do NOT return a JSON. Instead, ask follow-up questions to gather more details about the user's financial situation and goals.

        2. JSON Output (ONLY when enough info is collected):
        Return a JSON object at the VERY END with the following fields:
        - goal
        - affordability
        - recommended_action
        - monthly_savings_target
        - advice

        STRICT RULES FOR JSON:
        - Must be clean and human-readable
        - No abbreviations or slang

        IMPORTANT:
        - Do NOT explain the JSON
        - Do NOT include text after the JSON
        - JSON must be the LAST thing in the response
        - Before the JSON, end your message with:
        "Your personalised plan has been generated. Please see below for details."
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *chat_history
        ]
    )

    ai_message = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": ai_message})

    parsed_json = None
    try:
        start = ai_message.find("{")
        end = ai_message.rfind("}") + 1
        if start != -1 and end != -1:
            parsed_json = json.loads(ai_message[start:end])
    except:
        pass

    return jsonify({
        "reply": ai_message,
        "json": parsed_json
    })

if __name__ == "__main__":
    app.run(debug=True)