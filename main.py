import os
import json
from flask import Flask, request, jsonify
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

# --- Load Environment Variables ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
cred_json = os.getenv("FIREBASE_CREDENTIAL_JSON")
cred_dict = json.loads(cred_json)

# --- Initialize Flask ---
app = Flask(__name__)

# --- Initialize Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# --- Initialize Firebase ---
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_message = data.get("message")

    if not user_id or not user_message:
        return jsonify({"error": "Missing user_id or message"}), 400

    try:
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({"error": f"User ID '{user_id}' not found in Firestore."}), 404

        user_data = user_doc.to_dict()

        user_profile = f"""
Full Name: {user_data.get('fullName')}
DOB: {user_data.get('dateOfBirth')}
Gender: {user_data.get('gender')}
Blood Group: {user_data.get('bloodGroup')}
Allergies: {user_data.get('allergies')}
Medical Conditions: {user_data.get('medicalConditions')}
Medications: {user_data.get('medications')}
Fall History: {user_data.get('fallDescription')}
Sleep Hours: {user_data.get('sleepHours')}
Mobility Level: {user_data.get('mobilityLevel')}
"""

        prompt = f"""
You are a personalized AI medical assistant. The following is the user's health profile:

{user_profile}

Now answer the following user query safely and appropriately:
"{user_message}"
"""

        response = model.generate_content(prompt)
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
