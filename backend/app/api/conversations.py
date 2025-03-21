from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from app.core.auth import get_current_user
from app.models.user import User
from app.services.rag_service import rag_service

router = APIRouter()

# Create a new conversation
@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_conversation = Conversation(
        title=conversation.title,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

# Get all conversations for the current user
@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Conversation).filter(Conversation.user_id == current_user.id).all()

# Get a specific conversation by ID
@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

# Create a new message in a conversation
@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get conversation and verify ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create user message
    db_message = Message(
        content=message.content,
        role="user",
        conversation_id=conversation_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Get conversation history
    history = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.id != db_message.id  # Exclude the current message
    ).order_by(Message.created_at.asc()).all()
    
    # Format history for RAG service
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    try:
        # Get response from RAG service
        response_content = await rag_service.get_response(
            conversation_id=str(conversation_id),
            query=message.content,
            chat_history=chat_history,
            is_image_generation=message.is_image_generation if hasattr(message, 'is_image_generation') else False,
            is_web_search=message.is_web_search if hasattr(message, 'is_web_search') else False
        )

        # Create assistant message
        assistant_message = Message(
            content=response_content,
            role="assistant",
            conversation_id=conversation_id
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return assistant_message
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error generating response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the response"
        )

# Delete a conversation
@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Clean up RAG resources before deleting the conversation
    try:
        rag_service.cleanup_conversation(str(conversation_id))
    except Exception as e:
        print(f"Warning: Failed to clean up RAG resources for conversation {conversation_id}: {str(e)}")
    
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}

# Update the title of a conversation
@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db_conversation.title = conversation.title
    db.commit()
    db.refresh(db_conversation)
    return db_conversation 