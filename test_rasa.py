import requests
import json

RASA_API_URL = "https://educhatmind-rasa.onrender.com/webhooks/rest/webhook"

def test_rasa():
    payload = {
        "sender": "test_user",
        "message": "hello"
    }
    print(f"Sending message to {RASA_API_URL}...")
    try:
        response = requests.post(RASA_API_URL, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rasa()
