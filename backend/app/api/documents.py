from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.rag_service import rag_service
import os
import shutil
from typing import List
import uuid

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Create user-specific directory if it doesn't exist
        user_dir = os.path.join("Root", str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_dir, unique_filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the new document and update the vector store
        try:
            # Load and process the new document
            documents = rag_service.load_documents(user_dir)
            chunks = rag_service.split_documents(documents)
            
            # Update vector store with new chunks
            rag_service.vectorstore.add_documents(chunks)
            
            return {
                "id": str(uuid.uuid4()),  # Generate an ID for frontend reference
                "message": "File uploaded and processed successfully",
                "filename": file.filename
            }
        except Exception as e:
            # If processing fails, delete the uploaded file
            os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        ) 