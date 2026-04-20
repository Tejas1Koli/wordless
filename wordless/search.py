from wordless.indexer.embedder import embed
from wordless.indexer.store import search
from wordless import config


def search_code(query: str, callgraph: dict, hops: int = 2, repo_path: str | None = None) -> str:
    # 1. embed query
    q_embedding = embed([query])[0]
    
    # 2. vector search
    results = search(q_embedding, top_k=config.TOP_K, repo_path=repo_path)
    
    # Build reverse graph for callers
    reverse = {}
    for caller, callees in callgraph.items():
        for callee in callees:
            reverse.setdefault(callee, set()).add(caller)
    
    output = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    
    for doc, meta, dist in zip(docs, metas, distances):
        score = round(1 - dist, 2)  # chromadb returns distance, convert to similarity
        name = meta["name"]
        file = meta["file"]
        line = meta["line"]
        line_end = line + len(doc.splitlines())
        
        callers = sorted(reverse.get(name, set()))[:5]
        callees = sorted(callgraph.get(name, set()))[:5]
        
        # TOON format
        header = f"{name} ({file}:{line}-{line_end}) score:{score}"
        if callers:
            header += f" callers:{','.join(callers)}"
        if callees:
            header += f" callees:{','.join(callees)}"
        
        output.append(header)
        output.append(doc)
        output.append("---")
    
    return "\n".join(output)
