"""Centralized configuration for Wordless."""

from pathlib import Path
from wordless.config_manager import get

# History file for REPL
HISTORY_FILE = Path.home() / ".wordless_history"

# Cloud gateway configuration
API_KEY = get("api_key")
GATEWAY_URL = get("gateway_url", "http://localhost:8000")

# Repository
REPO_PATH = get("repo_path")

# Search parameters
TOP_K = get("top_k")
DEFAULT_HOPS = get("default_hops")

# Local storage (for vector DB)
DB_PATH = ".code_memory"
