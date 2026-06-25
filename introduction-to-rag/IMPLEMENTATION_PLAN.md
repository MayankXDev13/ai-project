# RAG Chat Application - Implementation Plan

Complete a RAG chat app: auth, PDF upload, background processing, RAG chat using LangChain + OpenAI + Qdrant + PostgreSQL.

## Files to Modify (8)
- `src/models/users.py` — add imports (Optional, List, Relationship)
- `src/models/documents.py` — make qdrant fields + title Optional
- `src/models/chats.py` — add missing imports + helpers
- `src/models/messages.py` — add missing imports + helpers
- `src/models/verificationtokens.py` — add imports + VerificationTokenType enum
- `src/db/database.py` — fix import path, remove SQLite connect_args
- `src/config/config.py` — add OPENAI_API_KEY, QDRANT_URL, UPLOAD_DIR
- `src/main.py` — add CORS, lifespan, routers

## Files to Create (18)
- Package inits (7): `src/__init__.py`, models/__init__.py, lib/__init__.py, routers/__init__.py, schemas/__init__.py, services/__init__.py, utils/__init__.py
- Auth (5): `lib/security.py`, `utils/dependencies.py`, `schemas/auth.py`, `services/auth_service.py`, `routers/auth.py`
- Documents (4): `schemas/documents.py`, `services/document_service.py`, `services/background.py`, `routers/documents.py`
- RAG + Chat (5): `services/rag_service.py`, `schemas/chat.py`, `routers/chat.py`

## Implementation Order
1. Package inits + model fixes — 7 files
2. Config + database + dependencies — 3 files
3. Security (lib + deps) — 2 files
4. Auth — 3 files
5. Documents — 4 files
6. RAG service — 1 file
7. Chat — 2 files
8. Wire main.py — 1 file
