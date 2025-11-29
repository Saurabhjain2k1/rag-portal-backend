# app/services/chat_service.py
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings
from app.ai import get_ai_provider


def get_retriever(tenant_id: int):
    collection_name = f"tenant_{tenant_id}"

    embeddings = HuggingFaceEmbeddings(
        model_name=settings.local_embed_model
    )

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )

    return vectorstore.as_retriever(search_kwargs={"k": 4})


def rag_answer(query: str, tenant_id: int):
    retriever = get_retriever(tenant_id)

    docs = retriever.invoke(query)

    context = "\n\n".join(
        f"[Doc {d.metadata.get('document_id', '?')}]\n{d.page_content}"
        for d in docs
    )

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use ONLY the provided context.",
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        },
    ]

    ai = get_ai_provider()
    answer = ai.chat(messages)

    return {
        "answer": answer,
        "sources": [
            {
                "document_id": d.metadata.get("document_id"),
                "text": d.page_content[:300] + "...",
            }
            for d in docs
        ],
    }
