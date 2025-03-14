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

        try:
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Process the document using RAG service
            print(f"Processing document: {file_path}")
            documents = rag_service.load_single_document(file_path, file.filename)
            print(f"Document loaded, pages: {len(documents)}")
            
            chunks = rag_service.split_documents(documents)
            print(f"Document split into chunks: {len(chunks)}")
            
            # Add chunks to vector store
            rag_service.vectorstore.add_documents(chunks)
            print("Chunks added to vector store")
            
            return {
                "id": str(uuid.uuid4()),
                "message": "File uploaded and processed successfully",
                "filename": file.filename
            }
        except Exception as e:
            # If processing fails, delete the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"Document processing error: {str(e)}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}\n{traceback.format_exc()}"
            )

    except Exception as e:
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}\n{traceback.format_exc()}"
        )

@router.get("/documents/test")
async def test_vectorstore(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Get a sample of documents from the vector store
        retriever = rag_service.vectorstore.as_retriever(search_kwargs={"k": 2})
        docs = retriever.get_relevant_documents("What is this document about?")
        
        return {
            "message": "Vector store test results",
            "document_samples": [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing vector store: {str(e)}"
        ) 