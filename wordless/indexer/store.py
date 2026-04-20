import chromadb
from wordless import config
import hashlib

client = chromadb.PersistentClient(path=config.DB_PATH)
collection = client.get_or_create_collection("code_chunks")

def _repo_id(repo_path: str) -> str:
    return hashlib.sha1(repo_path.encode("utf-8")).hexdigest()[:12]


def upsert(chunks, embeddings, repo_path: str):
    repo_id = _repo_id(repo_path)
    collection.upsert(
        ids=[f"{repo_id}:{c.file}:{c.line}:{c.name}" for c in chunks],
        embeddings=embeddings,
        documents=[c.source for c in chunks],
        metadatas=[
            {
                "name": c.name,
                "type": c.type,
                "file": c.file,
                "line": c.line,
                "repo_path": repo_path,
                "path_context": c.path_context,
            }
            for c in chunks
        ],
    )


def has_repo(repo_path: str) -> bool:
    result = collection.get(
        where={"repo_path": repo_path},
        limit=1,
    )
    return bool(result and result.get("ids"))


def search(query_embedding: list[float], top_k: int | None = None, repo_path: str | None = None):
    if top_k is None:
        top_k = config.TOP_K
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        **({"where": {"repo_path": repo_path}} if repo_path else {}),
    )