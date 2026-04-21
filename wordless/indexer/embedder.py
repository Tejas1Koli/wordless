import httpx
import ollama
from wordless import config


def embed(texts: list[str], path_contexts: list[str] = None) -> list[list[float]]:
    """Embed texts using configured provider (OpenAI/OpenRouter) with fallback to Ollama.
    
    Args:
        texts: List of code snippets to embed
        path_contexts: Optional list of file paths for context
    
    Returns:
        List of embeddings (float vectors)
    
    Provider priority:
        1. OpenAI (if api_key + embedding_provider=openai)
        2. OpenRouter (if api_key + embedding_provider=openrouter)
        3. Local Ollama (fallback)
    """
    api_key = config.API_KEY
    embedding_provider = getattr(config, 'EMBEDDING_PROVIDER', 'openai')
    
    # If path_contexts provided, prepend to texts for richer embedding
    if path_contexts is None:
        path_contexts = [""] * len(texts)

    # Prepare texts with context
    enriched_texts = [
        f"[{path_contexts[i]}]\n{text}" if path_contexts[i] else text
        for i, text in enumerate(texts)
    ]

    # Try API provider first
    if api_key:
        try:
            if embedding_provider == "openrouter":
                return _embed_with_openrouter(enriched_texts, api_key)
            else:  # default to openai
                return _embed_with_openai(enriched_texts, api_key)
        except (httpx.RequestError, httpx.TimeoutException):
            pass  # Fall through to Ollama

    # Fallback to local Ollama with qwen3-embedding:0.6b
    embeddings = []
    for text in enriched_texts:
        response = ollama.embed(model="qwen3-embedding:0.6b", input=text)
        embeddings.append(response.embeddings[0])
    return embeddings


def _embed_with_openai(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed using OpenAI API."""
    from wordless import config
    
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        json={
            "input": texts,
            "model": config.EMBEDDING_MODEL,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        timeout=60,
    )
    
    if response.status_code == 401:
        raise Exception("Invalid OpenAI API key. Run: wordless setup")
    if response.status_code == 200:
        data = response.json()
        embeddings_data = sorted(data.get("data", []), key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]
    else:
        raise Exception(f"OpenAI API error {response.status_code}: {response.text}")


def _embed_with_openrouter(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed using OpenRouter API."""
    from wordless import config
    
    response = httpx.post(
        "https://openrouter.ai/api/v1/embeddings",
        json={
            "input": texts,
            "model": config.EMBEDDING_MODEL,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://wordless.dev",
            "X-Title": "Wordless",
        },
        timeout=60,
    )
    
    if response.status_code == 401:
        raise Exception("Invalid OpenRouter API key. Run: wordless setup")
    if response.status_code == 200:
        data = response.json()
        embeddings_data = sorted(data.get("data", []), key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]
    else:
        raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")


def get_embedding_dimensions(provider: str = None, model: str = None) -> int:
    """Get the expected embedding dimensions for a provider/model.
    
    Returns:
        Dimension count (e.g., 1536 for OpenAI text-embedding-3-small, 1024 for nvidia models)
    """
    if provider is None:
        provider = getattr(config, 'EMBEDDING_PROVIDER', 'openai')
    if model is None:
        model = getattr(config, 'EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Known dimension mappings
    dimension_map = {
        # OpenAI models
        "openai:text-embedding-3-small": 1536,
        "openai:text-embedding-3-large": 3072,
        "openai:text-embedding-3-gigantic": 3072,
        # OpenRouter models
        "openrouter:openai/text-embedding-3-small": 1536,
        "openrouter:openai/text-embedding-3-large": 3072,
        "openrouter:cohere/embed-english-v3.0": 1024,
        "openrouter:nvidia/llama-nemotron-embed-vl-1b-v2:free": 1024,
        "openrouter:thenlper/gte-base": 768,
        "openrouter:thenlper/gte-small": 384,
        "openrouter:sentence-transformers/all-MiniLM-L6-v2": 384,
        "openrouter:sentence-transformers/all-mpnet-base-v2": 768,
        # Ollama models
        "ollama:qwen3-embedding:0.6b": 2560,
    }
    
    key = f"{provider}:{model}"
    if key in dimension_map:
        return dimension_map[key]
    
    # Default fallback
    if "openai" in provider.lower():
        return 1536
    elif "openrouter" in provider.lower():
        return 1024  # Most OpenRouter models
    elif "ollama" in provider.lower():
        return 2560
    else:
        return 1536  # Safe default
