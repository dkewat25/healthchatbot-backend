import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

# Load API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Flask
app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_message = data.get("message")

    if not user_id or not user_message:
        return jsonify({"error": "Missing user_id or message"}), 400

    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "User profile not found."}), 404

        profile = doc.to_dict()

        profile_prompt = f"""
You are a personalized AI health assistant. Here is the user's profile:

- Full Name: {profile.get('fullName')}
- Date of Birth: {profile.get('dateOfBirth')}
- Gender: {profile.get('gender')}
- Blood Group: {profile.get('bloodGroup')}
- Allergies: {profile.get('allergies')}
- Medical Conditions: {profile.get('medicalConditions')}
- Medications: {profile.get('medications')}
- Fall Description: {profile.get('fallDescription')}
- Sleep Hours: {profile.get('sleepHours')}
- Mobility Level: {profile.get('mobilityLevel')}

Now, answer this query safely:
"{user_message}"
"""

        response = model.generate_content(profile_prompt)
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
