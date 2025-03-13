# loaders.py
import os
import glob
import re
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP, ZH_CHUNK_SIZE, ZH_CHUNK_OVERLAP

def detect_language(text):
    """Simple language detection based on character sets"""
    # Check for presence of Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese_chars > len(text) * 0.2:  # If more than 20% Chinese characters are present
        return "zh"
    return "en" 

def add_metadata(doc, doc_type):
    doc.metadata["doc_type"] = doc_type
    # Detect language from document content
    doc.metadata["language"] = detect_language(doc.page_content)
    return doc

def load_documents(base_path="Root/*"):
    folders = glob.glob(base_path)
    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(folder, glob="**/*.pdf", loader_cls=PyPDFLoader)
        folder_docs = loader.load()
        documents.extend([add_metadata(doc, doc_type) for doc in folder_docs])
    
    return documents

def split_documents(documents):
    # Group documents by language
    en_docs = [doc for doc in documents if doc.metadata.get("language") == "en"]
    zh_docs = [doc for doc in documents if doc.metadata.get("language") == "zh"]
    other_docs = [doc for doc in documents if doc.metadata.get("language") not in ["en", "zh"]]
    
    # Different splitter configurations for different languages
    en_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    zh_splitter = RecursiveCharacterTextSplitter(
        chunk_size=ZH_CHUNK_SIZE,
        chunk_overlap=ZH_CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "，", "、", " ", ""]  # Chinese punctuation
    )
    
    # Split by language and combine results
    result_docs = []
    if en_docs:
        en_chunks = en_splitter.split_documents(en_docs)
        # print(f"English chunks: {len(en_chunks)}")
        result_docs.extend(en_chunks)
    if zh_docs:
        zh_chunks = zh_splitter.split_documents(zh_docs)
        # print(f"Chinese chunks: {len(zh_chunks)}")
        result_docs.extend(zh_chunks)
    if other_docs:
        other_chunks = en_splitter.split_documents(other_docs)
        # print(f"Other language chunks: {len(other_chunks)}")
        result_docs.extend(other_chunks)
        
    return result_docs