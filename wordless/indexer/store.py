import chromadb
from wordless import config
import hashlib

client = chromadb.PersistentClient(path=config.DB_PATH)
collection = client.get_or_create_collection("code_chunks")

def _repo_id(repo_path: str) -> str:
    return hashlib.sha1(repo_path.encode("utf-8")).hexdigest()[:12]


def _get_embedding_model_key() -> str:
    """Get unique key for current embedding model and its dimensions."""
    from wordless.indexer.embedder import get_embedding_dimensions
    provider = getattr(config, 'EMBEDDING_PROVIDER', 'openai')
    model = getattr(config, 'EMBEDDING_MODEL', 'text-embedding-3-small')
    dimensions = get_embedding_dimensions(provider, model)
    return f"{provider}:{model}:{dimensions}"


def _get_stored_model_key(repo_path: str) -> str | None:
    """Get the embedding model key used for a repo (from metadata of first chunk)."""
    try:
        result = collection.get(
            where={"repo_path": repo_path},
            limit=1,
        )
        if result and result.get("metadatas"):
            return result["metadatas"][0].get("embedding_model_key")
    except Exception:
        pass
    return None


def needs_reindex(repo_path: str) -> bool:
    """Check if repo needs re-indexing due to model/dimension change."""
    stored_key = _get_stored_model_key(repo_path)
    current_key = _get_embedding_model_key()
    
    if not stored_key:
        return False  # Repo not indexed yet, not a re-index
    
    return stored_key != current_key


def model_changed(repo_path: str) -> tuple[bool, str | None]:
    """Check if embedding model changed for a repo.
    
    Returns:
        (changed: bool, old_model_key: str | None)
    """
    stored_key = _get_stored_model_key(repo_path)
    current_key = _get_embedding_model_key()
    
    if stored_key and stored_key != current_key:
        return True, stored_key
    return False, stored_key


def clear_repo(repo_path: str) -> None:
    """Delete all embeddings for a repo (for re-indexing with new model)."""
    try:
        result = collection.get(where={"repo_path": repo_path})
        if result and result.get("ids"):
            collection.delete(ids=result["ids"])
    except Exception:
        pass


def upsert(chunks, embeddings, repo_path: str):
    repo_id = _repo_id(repo_path)
    embedding_model_key = _get_embedding_model_key()
    
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
                "embedding_model_key": embedding_model_key,  # NEW: Track model used
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