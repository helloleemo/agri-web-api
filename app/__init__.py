from pathlib import Path

from dotenv import load_dotenv


# Load project-level .env once when the app package is imported.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
