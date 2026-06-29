"""
=========================================================
Market Intelligence Monitor (MIM)
Configuration
=========================================================
"""

# Reuters Eikon
APP_KEY = ""

# Microsoft Teams
TEAMS_WEBHOOK_URL = ""

# Polling
POLL_INTERVAL = 30

# News
HEADLINE_COUNT = 20
PREVIEW_CHAR_LIMIT = 400
FRESHNESS_HOURS = 2

# Database
DATABASE_FILE = "database/market.db"

# Logging
LOG_FOLDER = "logs"

# Downloads
DOWNLOAD_FOLDER = "downloads/reports"

# Timezone
TIMEZONE = "Asia/Kolkata"

# Important Reuters urgency
IMPORTANT_URGENCY_LEVELS = {1, 2}

IMPORTANT_KEYWORDS = [
    "flash",
    "urgent",
    "breaking",
    "alert",
    "USDA",
    "WASDE",
    "grain stocks",
    "acreage",
    "crop progress",
    "export sales",
    "export inspections",
    "NOPA",
    "CONAB",
    "STATCAN",
    "COT",
]