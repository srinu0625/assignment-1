import os
import requests
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
SYMBOL = "ES"
DATA_URL = "https://tradingeconomics.com/stream?i=economy"  # Example URL, replace with actual data source
BASE_DIR = "market_data"
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# -----------------------
# SETUP
# -----------------------a
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
file_name = f"{SYMBOL}_{today}.csv"
file_path = os.path.join(DATA_DIR, file_name)
log_file = os.path.join(LOG_DIR, "download.log")

# -----------------------
# LOG FUNCTION
# -----------------------
def log(message):
    with open(log_file, "a") as f:
        f.write(f"{datetime.now()} | {message}\n")

# -----------------------
# MAIN LOGIC
# -----------------------
if os.path.exists(file_path):
    log(f"SKIPPED: {file_name} already exists")
    print("Data already downloaded. Skipping.")
else:
    try:
        response = requests.get(DATA_URL, timeout=15)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        log(f"SUCCESS: Downloaded {file_name}")
        print("Download successful.")

    except Exception as e:
        log(f"FAILED: {str(e)}")
        print("Download failed.")
