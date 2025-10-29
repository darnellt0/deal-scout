import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("CORS_ORIGINS", "[]")
os.environ.setdefault("SMTP_USE_TLS", "true")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "https://example.com/webhook")
