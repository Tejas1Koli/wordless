import httpx
from wordless import config


def embed(texts: list[str]) -> list[list[float]]:
    api_key = config.get("api_key")
    gateway_url = config.get("gateway_url", "http://localhost:8000")

    if not api_key:
        raise Exception("No API key set. Run: wordless config set api_key <your-key>")

    # wrap raw texts as minimal chunks
    chunks = [
        {
            "id": str(i),
            "name": f"chunk_{i}",
            "code": text,
            "file": "",
            "language": "python",
            "callers": [],
            "callees": [],
        }
        for i, text in enumerate(texts)
    ]

    response = httpx.post(
        f"{gateway_url}/embed",
        json={"chunks": chunks},
        headers={"x-api-key": api_key},
        timeout=60,
    )

    if response.status_code == 401:
        raise Exception("Invalid API key.")
    if response.status_code != 200:
        raise Exception(f"Gateway error {response.status_code}: {response.text}")

    return response.json()["embeddings"]    rm /Users/tejaskoli/wordless/wordless/backends/embedder.py
    rm /Users/tejaskoli/wordless/wordless/backends/store.py   # Also empty/unused