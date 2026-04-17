from wordless.indexer.embedder import embed
from wordless.indexer.store import search
from wordless.indexer.callgraph import expand
from wordless import config


def search_code(query: str, callgraph: dict, hops: int = None) -> str:
    if hops is None:
        hops = config.DEFAULT_HOPS
    
    # 1. embed query
    q_embedding = embed([query])[0]
    
    # 2. vector search
    results = search(q_embedding, top_k=config.TOP_K)
    
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append(f"# {meta['name']} ({meta['file']}:{meta['line']})")
        output.append(doc)
        
        # 3. expand with call graph
        related = expand(meta["name"], callgraph, hops=hops)
        if related:
            output.append(f"# related: {', '.join(related)}")
        
        output.append("---")
    print()
    return "\n".join(output)
