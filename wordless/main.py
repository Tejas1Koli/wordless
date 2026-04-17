from wordless.indexer.parser import index_repo
from wordless.indexer.embedder import embed
from wordless.indexer.store import upsert

repo_path = "/Users/tejaskoli/ollama-learn"
print("Parsing...")
chunks = index_repo(repo_path)
print(f"Found {len(chunks)} chunks, embedding...")
embeddings = embed([c.source for c in chunks])
print("Storing...")
upsert(chunks, embeddings)
print("Done.")