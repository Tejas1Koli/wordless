from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from openai import AsyncOpenAI
import os
from typing import Optional

app = FastAPI(title="Wordless Embedding Gateway")

openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

VALID_API_KEYS = set(os.environ.get("WORDLESS_API_KEYS", "").split(","))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


class Chunk(BaseModel):
    id: str
    name: str
    code: str
    file: str
    language: str = "python"
    callers: list[str] = []
    callees: list[str] = []


class EmbedRequest(BaseModel):
    chunks: list[Chunk]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    chunk_ids: list[str]


def verify_api_key(api_key: Optional[str]) -> None:
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")


def chunk_to_text(chunk: Chunk) -> str:
    """Convert a chunk to text for embedding."""
    parts = [
        f"File: {chunk.file}",
        f"Function: {chunk.name}",
    ]
    if chunk.callers:
        parts.append(f"Called by: {', '.join(chunk.callers)}")
    if chunk.callees:
        parts.append(f"Calls: {', '.join(chunk.callees)}")
    parts.append(f"\n{chunk.code}")
    return "\n".join(parts)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/embed", response_model=EmbedResponse)
async def embed(
    request: EmbedRequest,
    x_api_key: Optional[str] = Header(None),
):
    verify_api_key(x_api_key)

    if not request.chunks:
        raise HTTPException(status_code=400, detail="No chunks provided")

    if len(request.chunks) > 500:
        raise HTTPException(status_code=400, detail="Max 500 chunks per request")

    texts = [chunk_to_text(chunk) for chunk in request.chunks]

    # batch embed - openai handles up to 2048 inputs
    response = await openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
    )

    embeddings = [item.embedding for item in response.data]
    chunk_ids = [chunk.id for chunk in request.chunks]

    return EmbedResponse(
        embeddings=embeddings,
        model=EMBEDDING_MODEL,
        chunk_ids=chunk_ids,
    )