from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import rag_answer
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.post("/query", response_model=ChatResponse)
def chat_query(
    payload: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    RAG Chat endpoint - uses Chroma + Gemini
    """
    try:
        result = rag_answer(
            query=payload.query,
            tenant_id=current_user.tenant_id
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
