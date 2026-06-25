import uuid
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from langchain_core.messages import SystemMessage, HumanMessage
from pypdf import PdfReader
from src.lib.qdrant import client, ensure_collection
from src.config.config import OPENAI_API_KEY, OPENAI_BASE_URL


class RAGService:
    def __init__(self):
        headers = {
            "HTTP-Referer": "http://localhost:8001",
            "X-Title": "RAG Chat",
        }
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
            default_headers=headers,
        )
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
            default_headers=headers,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def process_pdf(self, file_path: str) -> list[LCDocument]:
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                pages.append(text)
        full_text = "\n\n".join(pages)
        return self.text_splitter.create_documents([full_text])

    def embed_and_store(self, docs: list[LCDocument], collection_name: str) -> int:
        if not docs:
            return 0

        ensure_collection(collection_name)
        texts = [doc.page_content for doc in docs]
        vectors = self.embeddings.embed_documents(texts)

        points = []
        for i, (vec, doc) in enumerate(zip(vectors, docs)):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": vec,
                "payload": {
                    "text": doc.page_content,
                    "chunk_index": i,
                },
            })

        client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def query(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 5,
    ) -> str:
        query_vector = self.embeddings.embed_query(query_text)
        results = client.query_points(
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

        response = self.llm.invoke(messages)
        return response.content
