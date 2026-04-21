from fastmcp import FastMCP
from wordless.search import search_code
from wordless.indexer.callgraph import build_callgraph
from wordless.indexer.parser import index_repo
from wordless.indexer.embedder import embed
from wordless.indexer.store import upsert, has_repo
from wordless import config
from wordless.config_manager import get_manager, set_config
from typing import Optional
from pathlib import Path

# Cache callgraphs per repo path to avoid rebuilding repeatedly
_callgraphs: dict[str, dict] = {}


def _resolve_repo_path(repo_path: Optional[str]) -> str:
    chosen = repo_path or config.REPO_PATH
    if not chosen:
        raise ValueError("No repo_path provided and config.REPO_PATH is not set")
    resolved = str(Path(chosen).expanduser().resolve())
    if not Path(resolved).exists():
        raise FileNotFoundError(f"Repository path not found: {resolved}")
    return resolved


def _save_indexed_repo(repo_path: str) -> None:
    manager = get_manager()
    indexed = manager.get("indexed_repos", []) or []
    repo_name = Path(repo_path).name
    existing_paths = {entry.get("path") for entry in indexed if isinstance(entry, dict)}
    if repo_path not in existing_paths:
        indexed.append({"name": repo_name, "path": repo_path})
        set_config("indexed_repos", indexed)


def _ensure_indexed(repo_path: str) -> None:
    if has_repo(repo_path):
        _save_indexed_repo(repo_path)
        return

    chunks = index_repo(repo_path)
    if not chunks:
        raise ValueError(f"No Python files found to index in repo: {repo_path}")
    embeddings = embed([c.source for c in chunks], path_contexts=[c.path_context for c in chunks])
    upsert(chunks, embeddings, repo_path=repo_path)
    _save_indexed_repo(repo_path)


def get_callgraph(repo_path: Optional[str] = None) -> dict:
    """Return a callgraph for `repo_path`, building and caching it if needed.

    If `repo_path` is None, falls back to `config.REPO_PATH`.
    Raises ValueError if no repo path is available.
    """
    repo_path = _resolve_repo_path(repo_path)
    if repo_path not in _callgraphs:
        _callgraphs[repo_path] = build_callgraph(repo_path)
    return _callgraphs[repo_path]


mcp = FastMCP("wordless")


@mcp.tool()
def search(query: str, repo_path: str, hops: Optional[int] = None) -> str:
    """Search the codebase semantically using natural language.
    
    Use this tool to find relevant functions, classes, or logic in the codebase
    without loading the entire repo into context. The tool will auto-index the
    repo on first search and cache the results for future queries.

    Args:
        query: A natural language description of what you're looking for.
               Examples:
               - "function that handles authentication and password validation"
               - "where is the database connection initialized"
               - "find all places where user input is validated"
        
        repo_path: Absolute path to the repository directory.
                   Required. Must exist on the file system.
                   Example: "/Users/tejas/my-project"

        hops: How many layers to expand in the call graph around results (default: 3).
              0 = return only matching code chunks
              1 = include direct callers and callees (recommended for initial search)
              2 = include callers of callers (use for understanding deep call flows)
              3+ = broader context but noisier results

    Returns:
        Formatted code chunks with file paths, line numbers, similarity score,
        and call graph relationships (callers/callees). Each result shows:
        - Function/class name and location
        - Source code snippet
        - Functions that call it (callers)
        - Functions it calls (callees)
        
        Use the results to understand the codebase. Follow up with more specific
        searches if you need different parts of the code.
    """
    if hops is None:
        hops = int(config.DEFAULT_HOPS)
    try:
        repo_path = _resolve_repo_path(repo_path)
        _ensure_indexed(repo_path)
        callgraph = get_callgraph(repo_path)
    except Exception as e:
        return f"Error building callgraph: {e}"
    return search_code(query, callgraph, hops=hops, repo_path=repo_path)


@mcp.tool()
def list_indexed_repos() -> list[dict]:
    """Return all repositories that have been indexed and are ready to search.
    
    Call this tool first if you don't know which repos are available or if you
    need to verify that a repository has already been indexed before calling search().
    
    Returns:
        List of indexed repositories as dicts with 'name' and 'path' keys.
        Example: [
            {"name": "my-project", "path": "/Users/tejas/my-project"},
            {"name": "utils", "path": "/Users/tejas/utils"}
        ]
        
        If the list is empty, no repos have been indexed yet. Call search() with
        a new repo_path to auto-index it.
    """
    manager = get_manager()
    indexed = manager.get("indexed_repos", []) or []
    return [entry for entry in indexed if isinstance(entry, dict) and entry.get("path")]


if __name__ == "__main__":
    mcp.run(transport="http", host=config.MCP_HOST, port=config.MCP_PORT)