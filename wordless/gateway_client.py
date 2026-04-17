import httpx
from dataclasses import dataclass


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


class GatewayClient:
    def __init__(self, api_key: str, gateway_url: str = "https://api.wordless.dev"):
        self.api_key = api_key
        self.gateway_url = gateway_url.rstrip("/")
        self.headers = {"x-api-key": api_key}

    def embed(self, chunks: list[Chunk], batch_size: int = 100) -> list[list[float]]:
        """Embed chunks in batches, return embeddings in same order."""
        all_embeddings = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            response = httpx.post(
                f"{self.gateway_url}/embed",
                json={"chunks": [c.to_dict() for c in batch]},
                headers=self.headers,
                timeout=60,
            )
            if response.status_code == 401:
                raise Exception("Invalid API key. Run: wordless config set api_key <your-key>")
            if response.status_code != 200:
                raise Exception(f"Gateway error {response.status_code}: {response.text}")

            data = response.json()
            all_embeddings.extend(data["embeddings"])

        return all_embeddings