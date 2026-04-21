"""Typer CLI application entry point for Wordless."""

import typer
from wordless.cli.commands import IndexManager
from wordless.cli.repl import REPL
from wordless.config_manager import get_manager

app = typer.Typer(
    help="🔍 Wordless: Semantic code search engine",
    no_args_is_help=True,
)
manager = IndexManager()
config_mgr = get_manager()


@app.command()
def repl() -> None:
    """Start interactive REPL mode."""
    repl = REPL()
    repl.run()


@app.command("repos")
def list_repos() -> None:
    """List all indexed repositories saved in configuration."""
    indexed = config_mgr.get("indexed_repos", []) or []
    repos = [entry for entry in indexed if isinstance(entry, dict) and entry.get("path")]

    if not repos:
        typer.echo("📦 No indexed repositories saved yet.")
        return

    typer.echo("\n📚 Indexed repositories:")
    typer.echo("─" * 60)
    for i, entry in enumerate(repos, start=1):
        name = entry.get("name") or "unknown"
        path = entry.get("path")
        typer.echo(f"{i}. {name}")
        typer.echo(f"   {path}")
    typer.echo("─" * 60)


@app.command()
def setup() -> None:
    """Interactive setup wizard for embeddings configuration.
    
    For detailed documentation, see: wordless/cli/SETUP_README.md
    
    This wizard will guide you through:
    - Choosing an embedding provider (OpenAI, OpenRouter, Ollama)
    - Entering and validating your API key
    - Selecting your preferred embedding model
    - Saving all settings automatically
    """
    typer.echo("\n🔧 Wordless Setup Wizard")
    typer.echo("─" * 60)
    
    # Step 1: Choose provider
    typer.echo("\n📌 Step 1: Choose Embedding Provider")
    typer.echo("1. OpenAI (Recommended - Best quality)")
    typer.echo("2. OpenRouter (Alternative - Multi-provider)")
    typer.echo("3. Local Ollama (Free - No API key needed)")
    
    choice = typer.prompt("Select option", type=int)
    
    if choice == 1:
        provider = "openai"
        api_url = "https://platform.openai.com/account/api-keys"
    elif choice == 2:
        provider = "openrouter"
        api_url = "https://openrouter.ai/keys"
    elif choice == 3:
        provider = "ollama"
        typer.echo("\n✅ Ollama configured!")
        typer.echo("   Make sure to install: ollama pull qwen3-embedding:0.6b")
        config_mgr.reset("api_key")
        config_mgr.reset("embedding_provider")
        typer.echo("\n✨ Setup complete!")
        return
    else:
        typer.echo("❌ Invalid option. Setup cancelled.")
        raise typer.Exit(code=1)
    
    # Step 2: Get API key
    typer.echo(f"\n📌 Step 2: API Key")
    typer.echo(f"Get your free API key at: {api_url}")
    
    api_key = typer.prompt("Enter your API key")
    if not api_key or len(api_key.strip()) == 0:
        typer.echo("❌ API key cannot be empty. Setup cancelled.")
        raise typer.Exit(code=1)
    
    # Step 3: Validate API key and fetch available models
    typer.echo("\n⏳ Validating API key and fetching available models...")
    if not _validate_api_key(api_key, provider):
        typer.echo(f"❌ API key validation failed. Please check your key and try again.")
        typer.echo(f"   Get a new key at: {api_url}")
        raise typer.Exit(code=1)
    
    typer.echo("✅ API key validated!")
    
    # Step 3: Get embedding model
    typer.echo(f"\n📌 Step 3: Embedding Model")
    if provider == "openai":
        typer.echo("   Examples: text-embedding-3-small, text-embedding-3-large")
    elif provider == "openrouter":
        typer.echo("   Examples:")
        typer.echo("   - openai/text-embedding-3-small")
        typer.echo("   - nvidia/llama-nemotron-embed-vl-1b-v2:free")
        typer.echo("   - thenlper/gte-base")
        typer.echo("   Visit: https://openrouter.ai/models?only=embedding for full list")
    
    model_prompt = "Enter embedding model name" if provider == "openai" else "Enter embedding model (from OpenRouter)"
    selected_model = typer.prompt(model_prompt)
    
    if not selected_model or len(selected_model.strip()) == 0:
        typer.echo("❌ Model name cannot be empty. Setup cancelled.")
        raise typer.Exit(code=1)
    
    # Step 5: Save configuration
    typer.echo("\n⏳ Saving configuration...")
    try:
        config_mgr.set("embedding_provider", provider)
        config_mgr.set("api_key", api_key)
        typer.echo("✅ Configuration saved!")
    except Exception as e:
        typer.echo(f"❌ Failed to save configuration: {e}")
        raise typer.Exit(code=1)
    
    # Step 6: Summary
    typer.echo("\n" + "=" * 60)
    typer.echo("✨ Setup Complete!")
    typer.echo("=" * 60)
    typer.echo(f"Provider: {provider}")
    typer.echo(f"API Key: {api_key[:10]}{'*' * (len(api_key) - 10)}")
    typer.echo(f"Model: {selected_model}")
    typer.echo("\n💡 You can now use Wordless to search your code!")
    typer.echo("   Try: wordless debug 'find parser functions'")
    typer.echo("=" * 60)


def _validate_api_key(api_key: str, provider: str) -> bool:
    """Validate API key by making a test request."""
    import httpx
    
    try:
        if provider == "openai":
            response = httpx.post(
                "https://api.openai.com/v1/embeddings",
                json={
                    "input": ["test"],
                    "model": "text-embedding-3-small",
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10,
            )
        elif provider == "openrouter":
            response = httpx.post(
                "https://openrouter.ai/api/v1/embeddings",
                json={
                    "input": ["test"],
                    "model": "openai/text-embedding-3-small",
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://wordless.dev",
                    "X-Title": "Wordless",
                },
                timeout=10,
            )
        else:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            typer.echo("   🔴 Invalid API key (401 Unauthorized)")
            return False
        elif response.status_code == 429:
            typer.echo("   🟡 Rate limited - but key seems valid")
            return True
        else:
            typer.echo(f"   🔴 API error: {response.status_code}")
            return False
    except httpx.TimeoutException:
        typer.echo("   🟡 Timeout - but key seems valid")
        return True
    except httpx.RequestError as e:
        typer.echo(f"   🔴 Network error: {e}")
        return False
    except Exception as e:
        typer.echo(f"   🔴 Validation error: {e}")
        return False


def _fetch_openai_models(api_key: str) -> list[str]:
    """Fetch available embedding models from OpenAI API."""
    import httpx
    
    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        # Filter for embedding models
        models = [
            model["id"] for model in data.get("data", [])
            if "embedding" in model["id"]
        ]
        
        # Prioritize recommended models
        recommended = ["text-embedding-3-small", "text-embedding-3-large"]
        sorted_models = sorted(
            models,
            key=lambda m: (m not in recommended, recommended.index(m) if m in recommended else 999)
        )
        
        return sorted_models if sorted_models else []
    except Exception as e:
        typer.echo(f"   ⚠️  Could not fetch OpenAI models: {e}")
        return []


def _fetch_openrouter_models(api_key: str) -> list[str]:
    """Get popular embedding models available via OpenRouter."""
    import httpx
    
    # Curated list of popular embedding models available through OpenRouter
    # These are proven to work with OpenRouter's embedding endpoint
    popular_models = [
        "openai/text-embedding-3-small",
        "openai/text-embedding-3-large",
        "cohere/embed-english-v3.0",
        "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        "thenlper/gte-base",
        "thenlper/gte-small",
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-mpnet-base-v2",
    ]
    
    # Try to validate API key works
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/embeddings",
            json={
                "input": ["test"],
                "model": "openai/text-embedding-3-small",
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://wordless.dev",
                "X-Title": "Wordless",
            },
            timeout=10,
        )
        
        # If successful, return the popular models
        if response.status_code == 200:
            return popular_models
            
    except Exception:
        pass
    
    return popular_models


def serve(port: int = typer.Option(None, "--port", "-p", help="Port to run on")) -> None:
    """Start MCP server for LLM integration."""
    try:
        from wordless.mcp_server import mcp
        from wordless import config
        
        if port is None:
            port = config.MCP_PORT
        
        typer.echo(f"🚀 Starting MCP server on {config.MCP_HOST}:{port}")
        mcp.run(transport="http", host=config.MCP_HOST, port=port)
    except Exception as e:
        typer.echo(f"❌ Error starting server: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def debug(
    query: str = typer.Argument(..., help="Search query"),
    repo_path: str = typer.Option(".", "--repo-path", "-r", help="Repository path to search in"),
) -> None:
    """Test semantic search directly without MCP. For development only."""
    try:
        from pathlib import Path
        from wordless.mcp_server import _ensure_indexed, get_callgraph
        from wordless.search import search_code
        
        # Resolve repo path
        resolved_path = str(Path(repo_path).expanduser().resolve())
        
        # Ensure indexed
        typer.echo(f"🔄 Ensuring repo is indexed: {resolved_path}")
        _ensure_indexed(resolved_path)
        
        # Get callgraph
        typer.echo(f"📊 Building call graph...")
        callgraph = get_callgraph(resolved_path)
        
        # Search
        typer.echo(f"🔍 Searching for: {query}\n")
        result = search_code(query, callgraph, repo_path=resolved_path)
        
        if result:
            typer.echo(result)
        else:
            typer.echo("No results found.")
    
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)



@app.command()
def config(
    action: str = typer.Argument(None, help="Action: set, get, list, reset, reset-all"),
    key: str = typer.Argument(None, help="Config key (for set/get/reset)"),
    value: str = typer.Argument(None, help="Config value (for set)"),
) -> None:
    """Manage Wordless configuration.
    
    For detailed documentation, see: wordless/cli/CONFIG_README.md
    
    Examples:
        wordless config set api_key sk-proj-YOUR_KEY
        wordless config get embedding_provider
        wordless config list
        wordless config reset top_k
        wordless config reset-all
    """
    if not action:
        typer.echo("Usage: wordless config [set|get|list|reset|reset-all] [key] [value]")
        typer.echo("\n💡 For detailed documentation, see: wordless/cli/CONFIG_README.md")
        typer.echo("   Or visit: https://github.com/Tejas1Koli/wordless/blob/main/wordless/cli/CONFIG_README.md")
        raise typer.Exit()

    try:
        if action == "set":
            if not key or value is None:
                typer.echo("❌ Usage: wordless config set <key> <value>")
                raise typer.Exit(code=1)
            
            # Type conversion for known types
            if key == "top_k":
                value = int(value)
            elif key == "default_hops":
                value = int(value)
            elif key == "mcp_port":
                value = int(value)
            
            config_mgr.set(key, value)
            typer.echo(f"✅ Set {key} = {value}")

        elif action == "get":
            if not key:
                typer.echo("❌ Usage: wordless config get <key>")
                raise typer.Exit(code=1)
            
            from wordless.config_manager import DEFAULTS
            if key not in DEFAULTS:
                typer.echo(f"❌ Unknown config key: {key}")
                raise typer.Exit(code=1)
            
            current_value = config_mgr.get(key)
            typer.echo(f"{key} = {current_value}")

        elif action == "list":
            from wordless.config_manager import DEFAULTS
            config_vals = config_mgr.list_all()
            
            typer.echo("\n📋 Wordless Configuration:")
            typer.echo("─" * 60)
            for key in sorted(config_vals.keys()):
                info = config_vals[key]
                current = info["current"]
                default = info["default"]
                indicator = "✓" if current == default else "✎"
                typer.echo(f"{indicator} {key:20} = {current}")
                if current != default:
                    typer.echo(f"  ({key:20}   default: {default})")
            typer.echo("─" * 60)

        elif action == "reset":
            if not key:
                typer.echo("❌ Usage: wordless config reset <key>")
                raise typer.Exit(code=1)
            
            from wordless.config_manager import DEFAULTS
            if key not in DEFAULTS:
                typer.echo(f"❌ Unknown config key: {key}")
                raise typer.Exit(code=1)
            
            default_val = DEFAULTS[key]
            config_mgr.reset(key)
            typer.echo(f"✅ Reset {key} to {default_val}")

        elif action == "reset-all":
            confirm = typer.confirm("Reset ALL configuration to defaults?")
            if confirm:
                config_mgr.reset_all()
                typer.echo("✅ All configuration reset to defaults")

        else:
            typer.echo(f"❌ Unknown action: {action}")
            typer.echo("Valid actions: set, get, list, reset, reset-all")
            typer.echo("\n💡 See CONFIG_README.md for detailed documentation.")
            raise typer.Exit(code=1)

    except ValueError as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def doctor() -> None:
    """Diagnostic tool to help debug Wordless setup issues."""
    from pathlib import Path
    import sys
    import chromadb
    
    typer.echo("\n🏥 Wordless Doctor - System Diagnostics")
    typer.echo("=" * 60)
    
    # 1. Python version
    typer.echo(f"\n✓ Python: {sys.version.split()[0]}")
    
    # 2. Configuration file
    from wordless import config
    config_file = Path.home() / ".wordless" / "config.json"
    if config_file.exists():
        typer.echo(f"✓ Config file: {config_file} ({config_file.stat().st_size} bytes)")
    else:
        typer.echo(f"⚠ Config file: NOT FOUND at {config_file}")
    
    # 3. Vector DB
    db_path = Path(config.DB_PATH)
    if db_path.exists():
        db_size = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file())
        typer.echo(f"✓ Vector DB: {db_path} ({db_size / 1024 / 1024:.2f} MB)")
        
        # Check ChromaDB connectivity
        try:
            client = chromadb.PersistentClient(path=config.DB_PATH)
            collections = client.list_collections()
            typer.echo(f"✓ ChromaDB: {len(collections)} collection(s) found")
            for col in collections:
                count = col.count()
                typer.echo(f"    - {col.name}: {count} vectors")
        except Exception as e:
            typer.echo(f"❌ ChromaDB error: {e}")
    else:
        typer.echo(f"⚠ Vector DB: NOT INITIALIZED at {db_path}")
    
    # 4. Indexed repos
    indexed = config_mgr.get("indexed_repos", []) or []
    repos = [e for e in indexed if isinstance(e, dict) and e.get("path")]
    typer.echo(f"✓ Indexed repos: {len(repos)}")
    for repo_entry in repos:
        typer.echo(f"    - {repo_entry.get('name')}: {repo_entry.get('path')}")
    
    # 5. API Key
    api_key = config.API_KEY
    if api_key:
        typer.echo(f"✓ API Key: Set ({len(api_key)} chars)")
    else:
        typer.echo(f"⚠ API Key: Not set (will use local Ollama fallback)")
    
    # 6. Gateway connectivity
    try:
        import httpx
        response = httpx.head(config.GATEWAY_URL, timeout=2)
        typer.echo(f"✓ Gateway: {config.GATEWAY_URL} (status: {response.status_code})")
    except (httpx.RequestError, httpx.TimeoutException):
        typer.echo(f"⚠ Gateway: {config.GATEWAY_URL} (unreachable, using Ollama)")
    except Exception as e:
        typer.echo(f"⚠ Gateway: Error checking {config.GATEWAY_URL}")
    
    # 7. MCP Server config
    typer.echo(f"✓ MCP Server: {config.MCP_HOST}:{config.MCP_PORT}")
    
    # 8. Key paths
    typer.echo(f"\n📁 Key paths:")
    typer.echo(f"   Config dir: {Path.home() / '.wordless'}")
    typer.echo(f"   Vector DB: {config.DB_PATH}")
    typer.echo(f"   Workspace: {Path.cwd()}")
    
    typer.echo("\n" + "=" * 60)
    typer.echo("✅ Doctor complete. See above for any warnings (⚠) or errors (❌).\n")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

