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
import traceback

router = APIRouter()

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = None
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )

        # Create user-specific directory if it doesn't exist
        user_dir = os.path.join("Root", str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_dir, unique_filename)

        # Save the file
        print(f"Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # Process the document using RAG service
            print(f"Processing document: {file_path}")
            documents = rag_service.load_single_document(file_path, file.filename)
            print(f"Document loaded, pages: {len(documents)}")
            
            chunks = rag_service.split_documents(documents)
            print(f"Document split into chunks: {len(chunks)}")
            
            # Add chunks to vector store
            print("Adding chunks to vector store...")
            rag_service.vectorstore.add_documents(chunks)
            
            # Persist the vector store
            print("Persisting vector store...")
            rag_service.vectorstore.persist()
            
            print(f"Vector store collection count after update: {rag_service.vectorstore._collection.count()}")
            
            return {
                "id": str(uuid.uuid4()),
                "message": "File uploaded and processed successfully",
                "filename": file.filename,
                "chunks_added": len(chunks)
            }
            
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            print(traceback.format_exc())
            # Clean up the uploaded file if processing fails
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )

    except Exception as e:
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        # Clean up the uploaded file if it exists
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        ) 