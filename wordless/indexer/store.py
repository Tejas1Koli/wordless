import chromadb
from chromadb.config import Settings
from wordless import config

client = chromadb.PersistentClient(path=config.DB_PATH)
collection = client.get_or_create_collection("code_chunks")

def upsert(chunks, embeddings):
    collection.upsert(
        ids=[f"{c.file}:{c.line}" for c in chunks],
        embeddings=embeddings,
        documents=[c.source for c in chunks],
        metadatas=[{"name": c.name, "type": c.type, "file": c.file, "line": c.line} for c in chunks],
    )

def search(query_embedding: list[float], top_k: int = None):
    if top_k is None:
        top_k = config.TOP_K
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )