"""Endpoints for reading calls.

GET /api/conversations        -> list of calls (optionally filtered by agent)
GET /api/conversations/{id}   -> one call with its full transcript
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Conversation
from app.schemas import ConversationDetail, ConversationSummary

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_conversations(agent_id: str | None = None, db: Session = Depends(get_db)):
    query = select(Conversation).order_by(Conversation.id)
    if agent_id:
        query = query.where(Conversation.agent_id == agent_id)
    return db.scalars(query).all()


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.turns))
    )
    conversation = db.scalars(query).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
