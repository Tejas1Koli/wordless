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
def index(repo_path: str = typer.Argument(..., help="Path to Python repository")) -> None:
    """Index a Python repository for semantic search."""
    try:
        manager.index(repo_path)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    hops: int = typer.Option(None, "--hops", "-h", help="Call graph expansion depth"),
) -> None:
    """Search the indexed codebase."""
    result = manager.search(query, hops=hops)
    typer.echo(result)


@app.command()
def repl() -> None:
    """Start interactive REPL mode."""
    repl = REPL()
    repl.run()


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


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

