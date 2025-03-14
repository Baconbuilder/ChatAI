from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import traceback

# Configuration
MODEL_NAME = "llama3.2:latest"
TEMPERATURE = 0.5
EMBEDDING_MODEL = "snowflake-arctic-embed2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
ZH_CHUNK_SIZE = 384
ZH_CHUNK_OVERLAP = 75

class RAGService:
    def __init__(self):
        self.vectorstore = None
        self.en_chain = None
        self.zh_chain = None
        self.embeddings = None
        self.setup_rag()

    def detect_language(self, text):
        """Detect if text is primarily in Chinese"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return "zh" if chinese_chars > len(text) * 0.2 else "en"

    def add_metadata(self, doc, filename):
        """Add metadata to document including language detection"""
        doc.metadata["filename"] = filename
        doc.metadata["language"] = self.detect_language(doc.page_content)
        return doc

    def load_single_document(self, file_path, filename):
        """Load a single PDF document"""
        try:
            print(f"Loading document from: {file_path}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            print(f"Document loaded successfully, pages: {len(documents)}")
            return [self.add_metadata(doc, filename) for doc in documents]
        except Exception as e:
            print(f"Error loading document: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Failed to load PDF: {str(e)}")

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
        try:
            # Initialize embeddings
            self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
            
            # Load or create vector store
            vector_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vector_db')
            os.makedirs(vector_db_path, exist_ok=True)
            
            print("Loading vector store...")
            self.vectorstore = Chroma(
                persist_directory=vector_db_path,
                embedding_function=self.embeddings
            )
            print(f"Vector store loaded successfully. Collection count: {self.vectorstore._collection.count()}")

            # Initialize LLM
            llm = ChatOllama(temperature=TEMPERATURE, model=MODEL_NAME)
            
            # Setup retriever with search type and score threshold
            retriever = self.vectorstore.as_retriever(
                search_kwargs={
                    "k": 4,
                    "search_type": "similarity",
                    "score_threshold": 0.5
                }
            )
            
            # Setup question condenser
            condense_template = (
                "Given a chat history and the latest user question "
                "which might reference context in the chat history, "
                "formulate a standalone question which can be understood "
                "without the chat history. Do NOT answer the question, "
                "just reformulate it if needed and otherwise return it as is.\n\n"
                "Chat History:\n{chat_history}\n\n"
                "Latest Question: {input}\n\n"
                "Standalone question:"
            )

            condense_prompt = ChatPromptTemplate.from_messages([
                ("system", condense_template),
                ("human", "{input}"),
            ])

            # Create history-aware retriever
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever=retriever, prompt=condense_prompt
            )

            # Setup language-specific chains with improved prompts
            en_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant that explains content from documents. "
                        "Use the following pieces of retrieved context to answer the user's question. "
                        "If you don't find the answer in the context, just say that you don't know. "
                        "Always maintain a helpful and professional tone.\n\n"
                        "Context:\n{context}\n\n"
                        "Chat History:\n{chat_history}\n\n"
                        "Question: {input}\n\n"
                        "Answer:"),
            ])
            
            zh_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一個專業的文件內容解讀助理。"
                        "請使用以下檢索到的文件內容來回答用戶的問題。"
                        "如果在文件中找不到答案，請直接說明你不知道。"
                        "請始終保持專業和友善的語氣。\n\n"
                        "文件內容：\n{context}\n\n"
                        "對話歷史：\n{chat_history}\n\n"
                        "問題：{input}\n\n"
                        "回答："),
            ])

            # Create document chains
            en_document_chain = create_stuff_documents_chain(llm, en_prompt)
            zh_document_chain = create_stuff_documents_chain(llm, zh_prompt)
            
            # Create retrieval chains
            self.en_chain = create_retrieval_chain(history_aware_retriever, en_document_chain)
            self.zh_chain = create_retrieval_chain(history_aware_retriever, zh_document_chain)
            
            print("RAG system initialized successfully")
            
        except Exception as e:
            print(f"Error setting up RAG system: {str(e)}")
            print(traceback.format_exc())
            raise

    async def get_response(self, query: str, chat_history: list = None) -> str:
        """Get response from the appropriate chain based on query language"""
        try:
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
            
            print(f"Processing query in {lang} language")
            print(f"Vector store collection count: {self.vectorstore._collection.count()}")
            
            # Get response
            response = await chain.ainvoke({
                "input": query,
                "chat_history": formatted_history
            })
            
            if not response.get("answer"):
                return "I apologize, but I couldn't find relevant information in the documents to answer your question."
            
            return response["answer"]
            
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            print(traceback.format_exc())
            return "I apologize, but I encountered an error while processing your question. Please try again."

# Initialize global RAG service
rag_service = RAGService() 