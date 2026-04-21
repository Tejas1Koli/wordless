import httpx
from dataclasses import dataclass
from wordless import config


@dataclass
class Chunk:
    id: str
    name: str
    code: str
    file: str
    language: str = "python"
    callers: list = None
    callees: list = None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "file": self.file,
            "language": self.language,
            "callers": self.callers or [],
            "callees": self.callees or [],
        }


class OpenAIEmbeddingClient:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Create OpenAI embedding client.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model (default: text-embedding-3-small)
                   Options: text-embedding-3-small, text-embedding-3-large
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def embed(self, chunks: list[Chunk], batch_size: int = 100) -> list[list[float]]:
        """Embed chunks using OpenAI API, batches automatically.
        
        Args:
            chunks: List of Chunk objects to embed
            batch_size: Number of chunks per request (max 2000 for OpenAI)
        
        Returns:
            List of embeddings (float vectors) in same order as input chunks
        """
        all_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            
            # Prepare texts from chunks (code + path context for better semantics)
            texts = [f"[{c.file}]\n{c.code}" for c in batch]
            
            try:
                response = httpx.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "input": texts,
                        "model": self.model,
                    },
                    headers=self.headers,
                    timeout=60,
                )
                
                if response.status_code == 401:
                    raise Exception("Invalid OpenAI API key. Run: wordless config set api_key <your-key>")
                if response.status_code == 429:
                    raise Exception("OpenAI rate limit exceeded. Try again later.")
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error {response.status_code}: {response.text}")
                
                data = response.json()
                
                # Extract embeddings from OpenAI response
                # OpenAI returns list of {"index": i, "embedding": [...], "object": "embedding"}
                embeddings_data = sorted(data.get("data", []), key=lambda x: x["index"])
                batch_embeddings = [item["embedding"] for item in embeddings_data]
                
                all_embeddings.extend(batch_embeddings)
                
            except httpx.RequestError as e:
                raise Exception(f"Network error connecting to OpenAI: {e}")
        
        return all_embeddings


class OpenRouterClient:
    def __init__(self, api_key: str, model: str = "openai/text-embedding-3-small"):
        """Create OpenRouter embedding client.
        
        Args:
            api_key: OpenRouter API key
            model: Embedding model (default: openai/text-embedding-3-small)
                   Available: openai/text-embedding-3-small, openai/text-embedding-3-large
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://wordless.dev",
            "X-Title": "Wordless",
        }

    def embed(self, chunks: list[Chunk], batch_size: int = 100) -> list[list[float]]:
        """Embed chunks using OpenRouter API, batches automatically.
        
        Args:
            chunks: List of Chunk objects to embed
            batch_size: Number of chunks per request (max 2000)
        
        Returns:
            List of embeddings (float vectors) in same order as input chunks
        """
        all_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            
            # Prepare texts from chunks
            texts = [f"[{c.file}]\n{c.code}" for c in batch]
            
            try:
                response = httpx.post(
                    f"{self.base_url}/embeddings",
                    json={
                        "input": texts,
                        "model": self.model,
                    },
                    headers=self.headers,
                    timeout=60,
                )
                
                if response.status_code == 401:
                    raise Exception("Invalid OpenRouter API key. Run: wordless config set api_key <your-key>")
                if response.status_code == 429:
                    raise Exception("OpenRouter rate limit exceeded. Try again later.")
                if response.status_code != 200:
                    raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
                
                data = response.json()
                
                # Extract embeddings from OpenRouter response (same format as OpenAI)
                embeddings_data = sorted(data.get("data", []), key=lambda x: x["index"])
                batch_embeddings = [item["embedding"] for item in embeddings_data]
                
                all_embeddings.extend(batch_embeddings)
                
            except httpx.RequestError as e:
                raise Exception(f"Network error connecting to OpenRouter: {e}")
        
        return all_embeddings


# Legacy alias for backward compatibility
class GatewayClient(OpenAIEmbeddingClient):
    """Backward compatibility wrapper. Use OpenAIEmbeddingClient instead."""
    pass