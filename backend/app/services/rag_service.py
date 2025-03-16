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
import shutil

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
        self.vectorstores = {}  # Dictionary to store vectorstores by conversation_id
        self.chains = {}  # Dictionary to store chains by conversation_id
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.base_vector_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vector_db')
        
        # Create base vector store directory if it doesn't exist
        if not os.path.exists(self.base_vector_path):
            os.makedirs(self.base_vector_path)

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
            # Group documents by language
            en_docs = [doc for doc in documents if doc.metadata.get("language") == "en"]
            zh_docs = [doc for doc in documents if doc.metadata.get("language") == "zh"]
            other_docs = [doc for doc in documents if doc.metadata.get("language") not in ["en", "zh"]]
            
            print(f"Documents by language - EN: {len(en_docs)}, ZH: {len(zh_docs)}, Other: {len(other_docs)}")
            
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

    def get_conversation_vector_path(self, conversation_id: str) -> str:
        """Get the vector store path for a specific conversation"""
        return os.path.join(self.base_vector_path, f"conversation_{conversation_id}")

    def setup_rag(self, conversation_id: str):
        """Initialize the RAG system for a specific conversation"""
        vector_db_path = self.get_conversation_vector_path(conversation_id)
        
        try:
            print(f"Setting up RAG for conversation {conversation_id}...")
            
            # Create vector store for this conversation
            self.vectorstores[conversation_id] = Chroma(
                persist_directory=vector_db_path,
                embedding_function=self.embeddings
            )
            print(f"Vector store initialized for conversation {conversation_id}")

            # Initialize LLM
            llm = ChatOllama(
                temperature=TEMPERATURE,
                model=MODEL_NAME
            )
            
            # Setup retriever
            retriever = self.vectorstores[conversation_id].as_retriever(search_kwargs={"k": 4})
            
            # Setup question condenser
            condense_question_system_template = (
                """You are a bilingual (English/Chinese) conversation assistant. Your task is to handle the chat history and latest question while being language-aware.

                Core Tasks:
                1. Identify the language of the current question (English/Chinese)
                2. Analyze the chat history in both languages
                3. Determine if this is a new question or truly a duplicate
                4. Handle context appropriately based on language patterns

                Guidelines for Question Processing:
                1. For English questions:
                   - Consider both English and Chinese context from history
                   - Reformulate while maintaining English grammar and structure
                   - Preserve any technical terms or proper nouns exactly as given

                2. For Chinese questions (中文問題處理):
                   - 同時考慮歷史中的中文和英文上下文
                   - 保持中文的語言習慣來重新表述
                   - 保留專有名詞的原始形式

                3. For questions that reference previous context:
                   - Include relevant context from both languages
                   - Maintain the current question's language in reformulation
                   - Preserve cross-language references when needed

                4. Duplicate Detection:
                   - Only mark as duplicate if exactly the same information is requested
                   - Consider language-specific variations as distinct questions
                   - A question asking for the same info in a different language is still a new question

                Output:
                - If it's a new question: Return the reformulated question in its original language
                - If it's truly a duplicate: Return "DUPLICATE: [original question]"
                - If it needs context: Return the reformulated question with necessary context
                
                Remember: Do NOT answer the question, just reformulate if needed or return as is."""
            )

            condense_question_prompt = ChatPromptTemplate.from_messages([
                ("system", condense_question_system_template),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])

            # Create history-aware retriever
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever=retriever, prompt=condense_question_prompt
            )

            # Create document chains with prompts
            en_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful and friendly AI assistant capable of both general conversation and document analysis.

                        Core principles:
                        1. Never make up information or statistics
                        2. If you don't know something, simply say so in a polite way
                        3. Be consistent with previous responses
                        4. If correcting a previous response, acknowledge the correction
                        5. Clearly distinguish between document-based and general knowledge

                        When responding to queries:
                        1. For document-specific queries:
                           - Draw from the provided documents
                           - If the information isn't in the documents, clearly state that
                           - Synthesize information accurately from the documents

                        2. For general knowledge queries:
                           - Provide accurate, factual information from your general knowledge
                           - Be clear that you're drawing from general knowledge, not the documents
                           - Maintain appropriate confidence levels about well-known facts vs. uncertain information

                        3. For all responses:
                           - Be natural and engaging
                           - Maintain a friendly, conversational tone
                           - Don't ask if the user wants to know about documents
                           - If mixing document and general knowledge, clearly distinguish between the two
                        
                        \n\n
                        {context}"""),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])
            
            zh_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一個專業且親切的AI助理，能夠進行一般對話並分析文件。

                        核心原則：
                        1. 絕不編造資訊或統計數據
                        2. 如果不知道答案，請禮貌的說不知道
                        3. 保持回答的一致性
                        4. 如果需要更正先前的回答，要明確說明
                        5. 清楚區分文件內容和一般知識
                        6. 請使用繁體中文進行回答，不要參雜其他語言，除非是文件中出現的專有名詞

                        回應查詢指南：
                        1. 針對文件相關查詢：
                           - 從提供的文件中提取資訊
                           - 如果文件中沒有相關資訊，請明確說明
                           - 準確綜合文件中的資訊

                        2. 針對一般知識查詢：
                           - 從AI助理的知識庫提供準確的資訊
                           - 明確說明是使用一般知識而非文件內容
                           - 對於確定的事實和不確定的資訊保持適當的信心程度

                        3. 所有回應原則：
                           - 保持自然友善的對話風格
                           - 維持輕鬆的對話氛圍
                           - 除非用戶特別詢問，否則不要主動詢問是否要了解文件內容
                           - 如果同時使用文件內容和一般知識，請清楚區分來源
                        
                        \n\n
                        {context}"""),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])

            en_document_chain = create_stuff_documents_chain(llm, en_prompt)
            zh_document_chain = create_stuff_documents_chain(llm, zh_prompt)
            
            # Store chains for this conversation
            self.chains[conversation_id] = {
                "en": create_retrieval_chain(history_aware_retriever, en_document_chain),
                "zh": create_retrieval_chain(history_aware_retriever, zh_document_chain)
            }
            
        except Exception as e:
            print(f"Error initializing RAG for conversation {conversation_id}: {str(e)}")
            print(traceback.format_exc())
            raise

    def cleanup_conversation(self, conversation_id: str):
        """Clean up resources for a specific conversation"""
        try:
            # Remove the vector store from memory
            if conversation_id in self.vectorstores:
                del self.vectorstores[conversation_id]
            
            # Remove the chains from memory
            if conversation_id in self.chains:
                del self.chains[conversation_id]
            
            # Remove the vector store directory
            vector_db_path = self.get_conversation_vector_path(conversation_id)
            if os.path.exists(vector_db_path):
                shutil.rmtree(vector_db_path)
                
            print(f"Cleaned up resources for conversation {conversation_id}")
        except Exception as e:
            print(f"Error cleaning up conversation {conversation_id}: {str(e)}")
            print(traceback.format_exc())

    def add_documents(self, conversation_id: str, documents):
        """Add documents to the vector store for a specific conversation"""
        try:
            # Initialize RAG for this conversation if not already done
            if conversation_id not in self.vectorstores:
                self.setup_rag(conversation_id)
            
            # Split documents if they haven't been split yet
            if hasattr(documents[0], 'page_content'):  # Check if documents need splitting
                documents = self.split_documents(documents)
            
            return self.vectorstores[conversation_id].add_documents(documents)
        except Exception as e:
            print(f"Error adding documents for conversation {conversation_id}: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Failed to add documents: {str(e)}")

    async def get_response(self, conversation_id: str, query: str, chat_history: list = None) -> str:
        """Get response from the appropriate chain based on query language"""
        if chat_history is None:
            chat_history = []
        
        try:
            # Initialize RAG for this conversation if not already done
            if conversation_id not in self.chains:
                self.setup_rag(conversation_id)
            
            print("\n=== Chat History Before Query ===")
            print(f"Conversation ID: {conversation_id}")
            for msg in chat_history:
                print(f"[{msg['role']}]: {msg['content']}")
            print(f"\n[Current Query]: {query}")
            
            # Format chat history using langchain Message objects
            formatted_history = []
            for msg in chat_history:
                if msg['role'] == 'user':
                    formatted_history.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    formatted_history.append(AIMessage(content=msg['content']))

            # Add logging for question processing
            print("\n=== Question Processing ===")
            print(f"Original question: {query}")
            print("Chat history length:", len(chat_history))
            print("Formatted history length:", len(formatted_history))
            
            # Log the last few messages from history if they exist
            if chat_history:
                print("\nRecent chat context:")
                for msg in chat_history[-3:]:  # Show last 3 messages
                    print(f"[{msg['role']}]: {msg['content'][:100]}...")  # Truncate long messages
            
            # Detect language and use appropriate chain
            lang = self.detect_language(query)
            chain = self.chains[conversation_id]["zh" if lang == "zh" else "en"]
            
            # Get response using the chain
            result = await chain.ainvoke({
                "input": query,
                "chat_history": formatted_history
            })
            
            # Get the response
            response = result["answer"] if isinstance(result, dict) else str(result)
            
            print("\n=== Chat History After Response ===")
            print(f"Conversation ID: {conversation_id}")
            for msg in chat_history:
                print(f"[{msg['role']}]: {msg['content']}")
            print(f"[user]: {query}")
            print(f"[assistant]: {response}")
            print("===========================\n")
            
            return response
        except Exception as e:
            error_msg = f"Error in get_response for conversation {conversation_id}: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

# Initialize global RAG service
rag_service = RAGService()