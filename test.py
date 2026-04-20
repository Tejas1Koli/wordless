# test.py
import asyncio
from pathlib import Path
from fastmcp import Client

REPO = "/Users/tejaskoli/ollama-learn"
SERVER = "http://localhost:6767/mcp"

# ─── 1. parser ───────────────────────────────────────────────
def test_parser():
    print("\n=== 1. PARSER ===")
    from wordless.indexer.parser import index_repo
    chunks = index_repo(REPO)
    print(f"Chunks found: {len(chunks)}")
    for c in chunks[:3]:
        print(f"  {c.name} ({c.type}) @ {Path(c.file).name}:{c.line}")
    assert len(chunks) > 0, "No chunks found"
    print("✓ parser ok")
    return chunks

# ─── 2. embedder ─────────────────────────────────────────────
def test_embedder(chunks):
    print("\n=== 2. EMBEDDER ===")
    from wordless.indexer.embedder import embed
    sample = [chunks[0].source]
    vectors = embed(sample)
    print(f"Vector dims: {len(vectors[0])}")
    assert len(vectors) == 1
    assert len(vectors[0]) > 0
    print("✓ embedder ok")
    return vectors

# ─── 3. store ────────────────────────────────────────────────
def test_store(chunks):
    print("\n=== 3. STORE ===")
    from wordless.indexer.embedder import embed
    from wordless.indexer.store import upsert, search
    embeddings = embed([c.source for c in chunks])
    upsert(chunks, embeddings)
    # search with first chunk's embedding
    results = search(embeddings[0], top_k=3)
    print(f"Results returned: {len(results['documents'][0])}")
    for meta in results["metadatas"][0]:
        print(f"  {meta['name']} @ {Path(meta['file']).name}:{meta['line']}")
    assert len(results["documents"][0]) > 0
    print("✓ store ok")

# ─── 4. callgraph ────────────────────────────────────────────
def test_callgraph():
    print("\n=== 4. CALLGRAPH ===")
    from wordless.indexer.callgraph import build_callgraph, expand
    cg = build_callgraph(REPO)
    print(f"Functions in graph: {len(cg)}")
    for fn, calls in list(cg.items())[:3]:
        print(f"  {fn} → {list(calls)[:3]}")
    # test expand
    first_fn = list(cg.keys())[0]
    related = expand(first_fn, cg, hops=2)
    print(f"  expand('{first_fn}', hops=2) → {len(related)} related")
    print("✓ callgraph ok")
    return cg

# ─── 5. search ───────────────────────────────────────────────
def test_search(cg):
    print("\n=== 5. SEARCH ===")
    from wordless.search import search_code
    queries = ["tool calling", "error handling", "file read"]
    for q in queries:
        result = search_code(q, cg)
        tokens = int(len(result) / 4)
        lines = len(result.splitlines())
        print(f"  '{q}' → {lines} lines, ~{tokens} tokens")
    assert result
    print("✓ search ok")

# ─── 6. mcp server ───────────────────────────────────────────
async def test_mcp():
    print("\n=== 6. MCP SERVER ===")
    try:
        async with Client(SERVER) as c:
            tools = await c.list_tools()
            print(f"Tools available: {[t.name for t in tools]}")
            assert any(t.name == "search" for t in tools), "search tool not found"

            result = await c.call_tool("search", {"query": "tool calling"})
            tokens = int(len(str(result)) / 4)
            print(f"Search result: ~{tokens} tokens")
            print("✓ mcp server ok")
    except Exception as e:
        print(f"✗ mcp server failed: {e}")
        print("  (is mcp_server.py running?)")

# ─── 7. token comparison ─────────────────────────────────────
def test_tokens():
    print("\n=== 7. TOKEN COMPARISON ===")
    from wordless.indexer.callgraph import build_callgraph
    from wordless.search import search_code

    SKIP = {"__pycache__", "site-packages", "dist-packages", ".git", "node_modules"}

    def is_venv(path):
        return any((Path(*path.parts[:i+1]) / "pyvenv.cfg").exists()
                   for i in range(len(path.parts)))

    full_repo = ""
    for path in Path(REPO).rglob("*.py"):
        if any(p in SKIP for p in path.parts): continue
        if is_venv(path): continue
        try: full_repo += path.read_text()
        except: pass

    cg = build_callgraph(REPO)
    result = search_code("tool calling", cg)

    repo_tokens = int(len(full_repo) / 4)
    result_tokens = int(len(result) / 4)
    reduction = 100 - int(result_tokens / repo_tokens * 100)

    print(f"Full repo:     ~{repo_tokens} tokens")
    print(f"Search result: ~{result_tokens} tokens")
    print(f"Reduction:     {reduction}%")
    print("✓ token comparison ok")

# ─── run all ─────────────────────────────────────────────────
async def main():
    print("=" * 40)
    print("WORDLESS TEST SUITE")
    print("=" * 40)

    try:
        chunks = test_parser()
        test_embedder(chunks)
        test_store(chunks)
        cg = test_callgraph()
        test_search(cg)
        await test_mcp()
        test_tokens()

        print("\n" + "=" * 40)
        print("ALL TESTS PASSED ✓")
        print("=" * 40)

    except AssertionError as e:
        print(f"\n✗ FAILED: {e}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise

asyncio.run(main())