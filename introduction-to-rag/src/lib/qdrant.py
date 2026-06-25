from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from src.config.config import QDRANT_URL

client = QdrantClient(url=QDRANT_URL)

COLLECTION_VECTOR_SIZE = 1536
COLLECTION_DISTANCE = Distance.COSINE

def ensure_collection(collection_name: str) -> None:
    collections = client.get_collections().collections
    existing = {c.name for c in collections}
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=COLLECTION_VECTOR_SIZE,
                distance=COLLECTION_DISTANCE,
            ),
        )

def delete_collection(collection_name: str) -> None:
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        client.delete_collection(collection_name)
