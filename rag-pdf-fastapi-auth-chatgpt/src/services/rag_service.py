import uuid
from functools import lru_cache
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from langchain_core.messages import SystemMessage, HumanMessage
from pypdf import PdfReader
from src.lib.qdrant import qdrant_client, ensure_collection
from src.config.config import OPENAI_API_KEY, OPENAI_BASE_URL

_headers = {
    "HTTP-Referer": "http://localhost:8001",
    "X-Title": "RAG Chat",
}


@lru_cache(maxsize=1)
def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL,
        default_headers=_headers,
    )


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL,
        default_headers=_headers,
    )


@lru_cache(maxsize=1)
def _get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def process_pdf(file_path: str) -> list[LCDocument]:
    reader = PdfReader(file_path)
    pages = [page.extract_text() for page in reader.pages if page.extract_text().strip()]
    full_text = "\n\n".join(pages)
    return _get_text_splitter().create_documents([full_text])


def embed_and_store(docs: list[LCDocument], collection_name: str) -> int:
    if not docs:
        return 0

    ensure_collection(collection_name)
    texts = [doc.page_content for doc in docs]
    vectors = _get_embeddings().embed_documents(texts)

    points = [
        {
            "id": str(uuid.uuid4()),
            "vector": vec,
            "payload": {
                "text": doc.page_content,
                "chunk_index": i,
            },
        }
        for i, (vec, doc) in enumerate(zip(vectors, docs))
    ]

    qdrant_client.upsert(collection_name=collection_name, points=points)
    return len(points)


def query(
    collection_name: str,
    query_text: str,
    top_k: int = 5,
) -> str:
    query_vector = _get_embeddings().embed_query(query_text)
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
    )

    if not results.points:
        return "No relevant context found in the document."

    context = "\n\n".join(
        f"[Chunk {r.payload.get('chunk_index', i)}]: {r.payload['text']}"
        for i, r in enumerate(results.points)
    )

    system_prompt = (
        "You are a helpful assistant answering questions based on the provided "
        "document context. Answer concisely and cite relevant parts. If the "
        "context doesn't contain enough information to answer, say so clearly."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query_text}"),
    ]

    response = _get_llm().invoke(messages)
    return response.content
