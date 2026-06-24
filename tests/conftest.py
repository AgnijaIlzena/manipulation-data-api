import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path so 'app' and 'olist_repository' are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable Sentry and MySQL before any import of app.py
sys.modules["sentry_sdk"] = MagicMock()
sys.modules["sentry_sdk.integrations"] = MagicMock()
sys.modules["sentry_sdk.integrations.flask"] = MagicMock()

os.environ.setdefault("SENTRY_DSN", "http://fake@sentry.io/0")
