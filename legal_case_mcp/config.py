import os

CASENOTE_EMAIL = os.environ.get("CASENOTE_EMAIL", "")
CASENOTE_PASSWORD = os.environ.get("CASENOTE_PASSWORD", "")
CASENOTE_BASE_URL = "https://casenote.kr"
HEADLESS = os.environ.get("CASENOTE_HEADLESS", "true").lower() == "true"
TIMEOUT_MS = int(os.environ.get("CASENOTE_TIMEOUT_MS", "30000"))
