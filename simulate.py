# simulate.py
import requests

CHATBOT_URL = "http://127.0.0.1:5000/chat"

def run_simulation():
    print("=== Health Chatbot CLI ===")
    user_id = input("Enter Firebase user_id: ")

    while True:
        message = input("You: ")
        if message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        payload = {"user_id": user_id, "message": message}
        try:
            response = requests.post(CHATBOT_URL, json=payload)
            if response.status_code == 200:
                print("Bot:", response.json()["response"])
            else:
                print("[Error]", response.status_code, response.text)
        except Exception as e:
            print("Connection error:", e)

if __name__ == "__main__":
    run_simulation()
