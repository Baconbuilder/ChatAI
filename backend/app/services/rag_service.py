from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import glob

# Configuration
MODEL_NAME = "llama3.2:latest"
TEMPERATURE = 0.5
EMBEDDING_MODEL = "snowflake-arctic-embed2"
DB_NAME = "vector_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
ZH_CHUNK_SIZE = 384
ZH_CHUNK_OVERLAP = 75

class RAGService:
    def __init__(self):
        self.vectorstore = None
        self.en_chain = None
        self.zh_chain = None
        self.setup_rag()

    def detect_language(self, text):
        """Detect if text is primarily in Chinese"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return "zh" if chinese_chars > len(text) * 0.2 else "en"

    def add_metadata(self, doc, doc_type):
        """Add metadata to document including language detection"""
        doc.metadata["doc_type"] = doc_type
        doc.metadata["language"] = self.detect_language(doc.page_content)
        return doc

    def load_documents(self, base_path="Root/*"):
        """Load PDF documents from the specified directory structure"""
        folders = glob.glob(base_path)
        documents = []
        for folder in folders:
            doc_type = os.path.basename(folder)
            loader = DirectoryLoader(folder, glob="**/*.pdf", loader_cls=PyPDFLoader)
            folder_docs = loader.load()
            documents.extend([self.add_metadata(doc, doc_type) for doc in folder_docs])
        return documents

    def split_documents(self, documents):
        """Split documents into chunks based on language"""
        # Group documents by language
        en_docs = [doc for doc in documents if doc.metadata.get("language") == "en"]
        zh_docs = [doc for doc in documents if doc.metadata.get("language") == "zh"]
        other_docs = [doc for doc in documents if doc.metadata.get("language") not in ["en", "zh"]]
        
        # Configure language-specific splitters
        en_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        zh_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ZH_CHUNK_SIZE,
            chunk_overlap=ZH_CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "，", "、", " ", ""]
        )
        
        # Split and combine results
        result_docs = []
        if en_docs:
            result_docs.extend(en_splitter.split_documents(en_docs))
        if zh_docs:
            result_docs.extend(zh_splitter.split_documents(zh_docs))
        if other_docs:
            result_docs.extend(en_splitter.split_documents(other_docs))
            
        return result_docs

    def setup_rag(self):
        """Initialize the RAG system"""
        # Initialize embeddings
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        # Load or create vector store
        vector_db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'vector_db')
        
        try:
            # Try to load existing documents
            print("Loading documents...")
            documents = self.load_documents()
            print("Splitting documents...")
            chunks = self.split_documents(documents)
            print(f"Total chunks: {len(chunks)}")
            
            # Create or update vector store
            if os.path.exists(vector_db_path):
                print("Updating existing vector store...")
                self.vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
                # Optionally update with new documents
                self.vectorstore.add_documents(chunks)
            else:
                print("Creating new vector store...")
                self.vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory=vector_db_path
                )
        except Exception as e:
            print(f"Error loading documents: {str(e)}")
            # Initialize empty vector store if loading fails
            print("Initializing empty vector store...")
            self.vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)

        # Initialize LLM
        llm = ChatOllama(temperature=TEMPERATURE, model=MODEL_NAME)
        
        # Setup retriever
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        
        # Setup question condenser
        condense_template = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        condense_prompt = ChatPromptTemplate.from_messages([
            ("system", condense_template),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever=retriever, prompt=condense_prompt
        )

        # Setup language-specific chains
        en_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that explains content from documents. "
                    "Provide accurate responses based on the available documents. "
                    "If you don't know the answer, just say that you don't know. "
                    "If the user doesn't ask for the source of the answer, don't provide the source of the answer."
                    "\n\n"
                    "{context}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        
        zh_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一個幫忙解釋文件內容的助理。"
                    "請根據可用文件提供可準確的回答。"
                    "如果你不知道答案，直接說你不知道。"
                    "如果使用者沒有要求回答的來源，請不要提供回答的來源。"
                    "請使用繁體中文進行回答。"
                    "\n\n"
                    "{context}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        # Create document chains
        en_document_chain = create_stuff_documents_chain(llm, en_prompt)
        zh_document_chain = create_stuff_documents_chain(llm, zh_prompt)
        
        # Create retrieval chains
        self.en_chain = create_retrieval_chain(history_aware_retriever, en_document_chain)
        self.zh_chain = create_retrieval_chain(history_aware_retriever, zh_document_chain)

    async def get_response(self, query: str, chat_history: list = None) -> str:
        """Get response from the appropriate chain based on query language"""
        if chat_history is None:
            chat_history = []
            
        # Format chat history for LangChain
        formatted_history = []
        for msg in chat_history:
            if msg['role'] == 'user':
                formatted_history.append(("human", msg['content']))
            elif msg['role'] == 'assistant':
                formatted_history.append(("assistant", msg['content']))

        # Detect language and use appropriate chain
        lang = self.detect_language(query)
        chain = self.zh_chain if lang == "zh" else self.en_chain
        
        # Get response
        response = await chain.ainvoke({
            "input": query,
            "chat_history": formatted_history
        })
        
        return response["answer"]

# Initialize global RAG service
rag_service = RAGService() 