import os
import time
from datetime import datetime

while True:
    now = datetime.now()
    day = now.strftime('Wednesday')        # Get day as 'Sunday'
    time_str = now.strftime('09:30')  # Get time as '10:00'

    if day == 'Wednesday' and time_str == '09:30':
        os.system("shutdown /r /f /t 0")  # Restart immediately, force all apps to close
        break

    time.sleep(30)  # Check every 30 seconds
