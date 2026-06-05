import requests
import time
from datetime import datetime

# ====== CONFIG ======
API_KEY = "1bd3f619408faa129e6effb6cac22eb9"
CITY    = " Hyderabad" 
WEBHOOK_URL = "https://default88ff9cb3e35e4d71b1d7f6c6ed8657.30.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/60b2e30fbc954d44a0ad6a2fbe958ce2/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b0w27fZV4iTXdMNFwd8HgbYeen3xyVdALXyf8HO-8Ac"

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "city": city,
            "temp": data["main"]["temp"],
            "desc": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"]
        }
    else:
        print("Error fetching weather:", response.text)
        return None

def post_to_teams(weather):
    # Use HTML <br> for line breaks
    message = {
        "message": (
            f"🌦 Weather Update: {weather['city']}<br>"
            f"Temperature: {weather['temp']}°C<br>"
            f"Condition: {weather['desc']}<br>"
            f"Humidity: {weather['humidity']}%<br>"
            f"Wind Speed: {weather['wind']} m/s<br>"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    }

    try:
        res = requests.post(WEBHOOK_URL, json=message, headers={"Content-Type": "application/json"})
        if res.status_code in [200, 202]:
            print(f"✅ Message sent at {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Error posting: {res.status_code} - {res.text}")
    except Exception as e:
        print("Exception while posting:", e)

if __name__ == "__main__":
    print("Weather bot started. Press Ctrl+C to stop.")
    while True:
        weather = get_weather(CITY)
        if weather:
            post_to_teams(weather)
        else:
            print("Skipping Teams post due to weather fetch error.")
        time.sleep(300)  # 5 minutes
