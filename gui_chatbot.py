import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Firebase
@st.cache_resource
def initialize_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Cache user profile
@st.cache_data(show_spinner=False)
def get_user_profile(uid):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None

# Save chat message to Firestore
def save_message(uid, sender, message):
    chat_ref = db.collection("users").document(uid).collection("chat_history")
    chat_ref.add({
        "sender": sender,
        "message": message,
        "timestamp": datetime.now()
    })

# Streamlit UI
st.set_page_config(page_title="Healthcare Chatbot", layout="centered")
st.title("🩺 Healthcare Chatbot")
uid = st.text_input("Enter your UID")

if uid:
    user_profile = get_user_profile(uid)

    if user_profile:
        st.success("User profile loaded ✅")

        if "chat_session" not in st.session_state:
            # Prepare context with minimal relevant info
            profile_summary = ", ".join(f"{k}: {v}" for k, v in user_profile.items())
            system_instruction = f"You are a helpful health assistant. The user profile is: {profile_summary}."
            st.session_state.chat_session = genai.GenerativeModel("gemini-1.5-flash").start_chat(history=[])
            st.session_state.chat_session.send_message(system_instruction)
            st.session_state.chat_history = []

        # Show history
        for entry in st.session_state.chat_history:
            with st.chat_message(entry["sender"]):
                st.markdown(entry["message"])

        user_input = st.chat_input("Ask a health-related question...")

        if user_input:
            # Show user input
            st.chat_message("user").markdown(user_input)
            st.session_state.chat_history.append({"sender": "user", "message": user_input})

            # Gemini response
            response = st.session_state.chat_session.send_message(user_input)
            bot_reply = response.text

            # Show and save bot reply
            st.chat_message("assistant").markdown(bot_reply)
            st.session_state.chat_history.append({"sender": "assistant", "message": bot_reply})

            # Save both messages to Firestore (optional: only last)
            save_message(uid, "user", user_input)
            save_message(uid, "assistant", bot_reply)
    else:
        st.error("User not found in Firestore ❌")
else:
    st.info("Please enter your UID to start chatting.")
