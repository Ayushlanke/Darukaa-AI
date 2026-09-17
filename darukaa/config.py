import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = REPO_ROOT / ".chroma"
DB_PATH = REPO_ROOT / "darukaa.db"

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Backward compatibility aliases
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or OPENROUTER_API_KEY
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", OPENROUTER_MODEL)

