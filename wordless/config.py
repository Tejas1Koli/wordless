"""Centralized configuration for Wordless."""

from pathlib import Path
from wordless.config_manager import get

# History file for REPL
HISTORY_FILE = Path.home() / ".wordless_history"

# Embedding provider configuration
API_KEY = get("api_key")
EMBEDDING_PROVIDER = get("embedding_provider", "openai")  # "openai" or "openrouter"
EMBEDDING_MODEL = get("embedding_model", "text-embedding-3-small")
GATEWAY_URL = get("gateway_url", "http://localhost:6768")  # Legacy

# Repository
REPO_PATH = get("repo_path")

# Search parameters
TOP_K = get("top_k")
DEFAULT_HOPS = get("default_hops")

# MCP server
MCP_HOST = get("mcp_host", "localhost")
MCP_PORT = get("mcp_port", 6767)

# Local storage (for vector DB) - use absolute path
DB_PATH = str(Path.home() / ".wordless" / "code_memory")
