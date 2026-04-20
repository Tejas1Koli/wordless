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
    
    Examples:
        wordless config set repo_path /path/to/repo
        wordless config get repo_path
        wordless config list
        wordless config reset repo_path
        wordless config reset-all
    """
    if not action:
        typer.echo("Usage: wordless config [set|get|list|reset|reset-all] [key] [value]")
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

