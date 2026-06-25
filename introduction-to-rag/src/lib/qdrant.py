from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from src.config.config import QDRANT_URL

qdrant_client = QdrantClient(url=QDRANT_URL)

COLLECTION_VECTOR_SIZE = 1536
COLLECTION_DISTANCE = Distance.COSINE

def ensure_collection(collection_name: str) -> None:
    collections = qdrant_client.get_collections().collections
    existing = {c.name for c in collections}
    if collection_name not in existing:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=COLLECTION_VECTOR_SIZE,
                distance=COLLECTION_DISTANCE,
            ),
        )

def delete_collection(collection_name: str) -> None:
    collections = qdrant_client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        qdrant_client.delete_collection(collection_name)
