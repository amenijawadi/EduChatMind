import requests

RASA_STATUS_URL = "https://educhatmind-rasa.onrender.com/status"

def check_status():
    print(f"Checking status at {RASA_STATUS_URL}...")
    try:
        response = requests.get(RASA_STATUS_URL, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
