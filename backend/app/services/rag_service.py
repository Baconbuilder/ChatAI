from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import traceback
import glob

# Configuration - Exactly matching reference implementation
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
        self.setup_rag()

    def detect_language(self, text):
        """Detect if text is primarily in Chinese"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return "zh" if chinese_chars > len(text) * 0.2 else "en"

    def add_metadata(self, doc, filename):
        """Add metadata to document including language detection"""
        doc.metadata["filename"] = filename
        doc.metadata["language"] = self.detect_language(doc.page_content)
        doc.metadata["doc_type"] = os.path.basename(os.path.dirname(filename))
        return doc

    def load_single_document(self, file_path, filename):
        """Load a single PDF document with robust error handling"""
        try:
            print(f"Loading document from: {file_path}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            print(f"Document loaded successfully, pages: {len(documents)}")
            
            processed_docs = []
            for doc in documents:
                if not doc.page_content.strip():
                    continue
                if len(doc.page_content.split()) < 10:
                    continue
                doc = self.add_metadata(doc, filename)
                processed_docs.append(doc)
                
            print(f"Processed {len(processed_docs)} non-empty pages")
            return processed_docs
        except Exception as e:
            error_msg = f"Error loading document {filename}: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

    def split_documents(self, documents):
        """Split documents into chunks based on language"""
        try:
            # Group documents by language - exactly matching reference
            en_docs = [doc for doc in documents if doc.metadata.get("language") == "en"]
            zh_docs = [doc for doc in documents if doc.metadata.get("language") == "zh"]
            other_docs = [doc for doc in documents if doc.metadata.get("language") not in ["en", "zh"]]
            
            print(f"Documents by language - EN: {len(en_docs)}, ZH: {len(zh_docs)}, Other: {len(other_docs)}")
            
            # Configure language-specific splitters - exactly matching reference
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
            
            result_docs = []
            if en_docs:
                result_docs.extend(en_splitter.split_documents(en_docs))
            if zh_docs:
                result_docs.extend(zh_splitter.split_documents(zh_docs))
            if other_docs:
                result_docs.extend(en_splitter.split_documents(other_docs))
            
            return result_docs
        except Exception as e:
            error_msg = f"Error splitting documents: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

    def setup_rag(self):
        """Initialize the RAG system"""
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vector_db')
        
        try:
            print("Loading vector store...")
            if os.path.exists(vector_db_path):
                print("Clearing existing vector store...")
                Chroma(persist_directory=vector_db_path, embedding_function=embeddings).delete_collection()
            
            # Create vector store - matching reference implementation
            self.vectorstore = Chroma(
                persist_directory=vector_db_path,
                embedding_function=embeddings
            )
            print("Vector store initialized")
        except Exception as e:
            print(f"Error initializing vector store: {str(e)}")
            print(traceback.format_exc())
            raise

        # Initialize LLM - exactly matching reference
        llm = ChatOllama(
            temperature=TEMPERATURE,
            model=MODEL_NAME
        )
        
        # Setup retriever - exactly matching reference
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        
        # Setup question condenser - exactly matching reference
        condense_question_system_template = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        condense_question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", condense_question_system_template),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ]
        )

        # Create history-aware retriever - exactly matching reference
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever=retriever, prompt=condense_question_prompt
        )

        # English prompt template - exactly matching reference
        en_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that explains content from documents. "
                    "Provide accurate responses based on the available documents. "
                    "If you don't know the answer, just say that you don't know."
                    "If the user doesnt ask for the source of the answer, don't provide the source of the answer."
                    "\n\n"
                    "{context}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        
        # Chinese prompt template - exactly matching reference
        zh_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一個幫忙解釋文件內容的助理。"
                    "請根據可用文件提供可準確的回答。"
                    "如果你不知道答案，直接說你不知道"
                    "如果使用者沒有要求回答的來源，請不要提供回答的來源。"
                    "請使用繁體中文進行回答。"
                    "\n\n"
                    "{context}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        # Create document chains - exactly matching reference
        en_document_chain = create_stuff_documents_chain(llm, en_prompt)
        zh_document_chain = create_stuff_documents_chain(llm, zh_prompt)
        
        # Create retrieval chains - exactly matching reference
        self.en_chain = create_retrieval_chain(history_aware_retriever, en_document_chain)
        self.zh_chain = create_retrieval_chain(history_aware_retriever, zh_document_chain)

    def add_documents(self, documents):
        """Add documents to the vector store using the reference implementation method"""
        try:
            return self.vectorstore.add_documents(documents)
        except Exception as e:
            print(f"Error adding documents: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Failed to add documents: {str(e)}")

    async def get_response(self, query: str, chat_history: list = None) -> str:
        """Get response from the appropriate chain based on query language"""
        if chat_history is None:
            chat_history = []
        
        try:
            # Format chat history using langchain Message objects - matching reference
            formatted_history = []
            for msg in chat_history:
                if msg['role'] == 'user':
                    formatted_history.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    formatted_history.append(AIMessage(content=msg['content']))

            # Detect language and use appropriate chain - exactly matching reference
            lang = self.detect_language(query)
            chain = self.zh_chain if lang == "zh" else self.en_chain
            
            # Get response using the chain
            result = await chain.ainvoke({
                "input": query,
                "chat_history": formatted_history
            })
            
            # Handle response with type checking - matching reference
            return result["answer"] if isinstance(result, dict) else str(result)
        except Exception as e:
            error_msg = f"Error in get_response: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

# Initialize global RAG service
rag_service = RAGService() 