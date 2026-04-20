import httpx
import ollama
from wordless import config


def embed(texts: list[str], path_contexts: list[str] = None) -> list[list[float]]:
    api_key = config.API_KEY
    gateway_url = config.GATEWAY_URL
    
    # If path_contexts provided, prepend to texts for richer embedding
    if path_contexts is None:
        path_contexts = [""] * len(texts)

    # wrap raw texts as minimal chunks
    chunks = [
        {
            "id": str(i),
            "name": f"chunk_{i}",
            "code": f"[{path_contexts[i]}]\n{text}" if path_contexts[i] else text,
            "file": "",
            "language": "python",
            "callers": [],
            "callees": [],
        }
        for i, text in enumerate(texts)
    ]

    # Try cloud gateway first
    if api_key:
        try:
            response = httpx.post(
                f"{gateway_url}/embed",
                json={"chunks": chunks},
                headers={"x-api-key": api_key},
                timeout=60,
            )
            if response.status_code == 401:
                raise Exception("Invalid API key.")
            if response.status_code == 200:
                return response.json()["embeddings"]
        except (httpx.RequestError, httpx.TimeoutException):
            pass  # Fall through to Ollama

    # Fallback to local Ollama with qwen3:0.6b
    embeddings = []
    for chunk in chunks:
        response = ollama.embed(model="qwen3-embedding:0.6b", input=chunk["code"])
        embeddings.append(response.embeddings[0])
    return embeddings