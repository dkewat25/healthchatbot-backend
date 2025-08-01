from user_profile import get_user_profile, build_prompt_context
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the UID you want to test with (from your Firebase)
test_uid = "NATLeusPobTxrqTNNyydVFQJHsi1"  # replace with real UID from your Firestore

# Fetch user profile
profile = get_user_profile(test_uid)

# Generate and print prompt
prompt = build_prompt_context(profile)
print("\n--- AI Prompt Generated from Firebase User Profile ---\n")
print(prompt)
