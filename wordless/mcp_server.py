from fastmcp import FastMCP
from wordless.search import search_code
from wordless.indexer.callgraph import build_callgraph
from wordless import config

REPO_PATH = config.REPO_PATH
callgraph = build_callgraph(REPO_PATH)

mcp = FastMCP("wordless")

@mcp.tool()
def search(query: str, hops: int = None) -> str:
    """Search the codebase semantically. Returns relevant functions with source code."""
    if hops is None:
        hops = config.DEFAULT_HOPS
    return search_code(query, callgraph, hops=hops)

if __name__ == "__main__":
    mcp.run(transport="http", host=config.MCP_HOST, port=config.MCP_PORT)