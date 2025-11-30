# app/services/ingest_langchain.py
import os
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.services.url_loader import load_url_with_bs4  # 👈 our BS4-based URL loader


def select_loader(path: str):
    """
    Auto-selects a LangChain loader based on file extension.
    Heavy langchain_community imports happen INSIDE this function
    so they don't run at app startup (important for Render).
    """
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        UnstructuredMarkdownLoader,
        UnstructuredWordDocumentLoader,
        UnstructuredCSVLoader,
        JSONLoader,
    )

    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(path)
    elif ext == ".txt":
        return TextLoader(path)
    elif ext == ".md":
        return UnstructuredMarkdownLoader(path)
    elif ext == ".docx":
        return UnstructuredWordDocumentLoader(path)
    elif ext == ".csv":
        return UnstructuredCSVLoader(path)
    elif ext == ".json":
        return JSONLoader(path, jq_schema=".", text_content=False)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def ingest_with_langchain(db: Session, document: Document, tenant_id: int) -> int:
    """
    Full LangChain ingestion using:
      - Local HuggingFace embeddings
      - Chroma as vector store
      - Files (pdf/txt/md/docx/csv/json) OR URLs

    All heavy imports are inside this function so that they DON'T
    run during app startup on Render.
    """
    # 🔁 Heavy imports moved here (lazy)
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    path = document.storage_path

    # 1) Load docs: URL vs file
    if path.startswith("http://") or path.startswith("https://"):
        # Uses requests + BeautifulSoup via our helper
        docs = load_url_with_bs4(path)
    else:
        loader = select_loader(path)
        docs = loader.load()

    # 2) Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)

    for c in chunks:
        c.metadata["tenant_id"] = tenant_id
        c.metadata["document_id"] = document.id

    # 3) Local embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.local_embed_model
    )

    # 4) Chroma vector store
    collection_name = f"tenant_{tenant_id}"
    persist_dir = settings.chroma_dir

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir,
    )

    return len(chunks)
