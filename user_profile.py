# user_profile.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_user_profile(uid):
    db = initialize_firestore()
    doc_ref = db.collection('users').document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    return doc.to_dict()

def build_prompt_context(profile):
    if not profile:
        return "User data not available."

    return f"""
You are a helpful AI medical assistant. The following is the user profile:

- Name: {profile.get('fullName')}
- Age: (calculate from DOB: {profile.get('dateOfBirth')})
- Gender: {profile.get('gender')}
- Blood Group: {profile.get('bloodGroup')}
- Medical Conditions: {profile.get('medicalConditions')}
- Allergies: {profile.get('allergies')}
- Medications: {profile.get('medications')}
- Has Previous Falls: {profile.get('hasPreviousFalls')}
- Fall Description: {profile.get('fallDescription')}
- Sleep Hours: {profile.get('sleepHours')}
- Activity Level: {profile.get('activityLevel')}
- Mobility Level: {profile.get('mobilityLevel')}
- Living Alone: {profile.get('livingAlone')}
- Height: {profile.get('height')} cm
- Weight: {profile.get('weight')} kg
- Language: {profile.get('language')}
    """.strip()
