# api.py

import os
import uvicorn
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- INITIALIZATION ---

# Initialize FastAPI app
app = FastAPI()

# Load API Key from environment variables
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("ERROR: GOOGLE_API_KEY environment variable not set.")
    exit()

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- DATA MODELS ---

class ChatRequest(BaseModel):
    user_id: str
    message: str

# Updated model to better match your Firestore structure
class UserProfile(BaseModel):
    name: str
    dateOfBirth: str # Storing date of birth is more robust than age
    health_goals: Optional[str] = None


# --- API ENDPOINTS ---

@app.post("/profile/{user_id}")
async def create_or_update_profile(user_id: str, profile: UserProfile):
    """
    Creates a new user profile or updates an existing one in Firestore.
    """
    try:
        # CORRECTED: Looking in the 'users' collection now
        profile_ref = db.collection('users').document(user_id)
        profile_ref.set(profile.dict(), merge=True) # Use merge to avoid overwriting other fields
        return {"status": "success", "user_id": user_id, "data": profile.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """
    Fetches a user's profile from Firestore.
    """
    try:
        # CORRECTED: Looking in the 'users' collection now
        profile_ref = db.collection('users').document(user_id)
        profile_doc = profile_ref.get()
        if profile_doc.exists:
            return {"status": "success", "user_id": user_id, "data": profile_doc.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_handler(request: ChatRequest):
    """
    Handles a chat message, personalizing the bot's instructions
    with the user's profile data from Firestore.
    """
    try:
        # --- 1. FETCH USER PROFILE ---
        # CORRECTED: Looking in the 'users' collection now
        profile_ref = db.collection('users').document(request.user_id)
        profile_doc = profile_ref.get()
        
        # --- 2. DYNAMICALLY CREATE SYSTEM INSTRUCTION ---
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            user_name = profile_data.get("name", "the user")
            user_goals = profile_data.get("health_goals", "general wellness")
            
            # IMPROVEMENT: Calculate age from dateOfBirth
            user_age = "an unknown age"
            dob_str = profile_data.get("dateOfBirth")
            if dob_str:
                try:
                    # Assuming format "DD/MM/YYYY"
                    birth_date = datetime.strptime(dob_str, "%d/%m/%Y")
                    today = datetime.today()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    user_age = f"{age} years old"
                except ValueError:
                    user_age = "an unknown age (invalid date format)"

            system_instruction = f"""You are a helpful and friendly AI Health Assistant.
            You are currently speaking with {user_name}, who is {user_age}. Their main health goal is: '{user_goals}'.
            Use this information to personalize your conversation. For example, you can address them by their name.

            You are not a doctor. You must always remind the user to consult with a real healthcare professional for any medical advice or diagnosis."""
        else:
            system_instruction = """You are a helpful and friendly AI Health Assistant.
            You should encourage the user to create a profile to get personalized advice.

            You are not a doctor. You must always remind the user to consult with a real healthcare professional for any medical advice or diagnosis."""

        # --- 3. LOAD CHAT HISTORY ---
        chat_history_ref = db.collection('chats').document(request.user_id)
        chat_history_doc = chat_history_ref.get()
        chat_history = []
        if chat_history_doc.exists:
            history_data = chat_history_doc.to_dict().get('history', [])
            for item in history_data:
                role = item.get('role')
                message = item.get('message')
                if role and message:
                    gemini_role = 'model' if role == 'assistant' else role
                    chat_history.append({'role': gemini_role, 'parts': [message]})
        
        # --- 4. CALL GEMINI WITH DYNAMIC INSTRUCTION ---
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_instruction
        )
        chat_session = model.start_chat(history=chat_history)

        response = chat_session.send_message(request.message)
        bot_reply = response.text

        # --- 5. SAVE CONVERSATION ---
        # CORRECTED: Using datetime.utcnow() as firestore.SERVER_TIMESTAMP is not supported in ArrayUnion.
        current_utc_time = datetime.utcnow()
        chat_history_ref.set({
            'history': firestore.ArrayUnion([
                {
                    'role': 'user', 
                    'message': request.message, 
                    'timestamp': current_utc_time
                },
                {
                    'role': 'assistant', 
                    'message': bot_reply, 
                    'timestamp': current_utc_time
                }
            ])
        }, merge=True)

        return {"reply": bot_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
