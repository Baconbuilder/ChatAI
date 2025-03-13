# vectorstore.py
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import DB_NAME, EMBEDDING_MODEL

def create_vectorstore(documents, db_name=DB_NAME):
    # Use a multilingual embedding model
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    print(f"Using embeddings model: {EMBEDDING_MODEL}")
    
    # Clear existing collection if it exists
    if os.path.exists(db_name):
        # print(f"Removing existing vector store at {db_name}")
        Chroma(persist_directory=db_name, embedding_function=embeddings).delete_collection()
    
    # Create new vector store with language metadata
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings,
        persist_directory=db_name,
        # Include language in collection metadata for potential filtering
        # collection_metadata={"languages": ["en", "zh"]}
    )
    # print(f"Vector store created with {len(documents)} chunks")
    return vectorstore