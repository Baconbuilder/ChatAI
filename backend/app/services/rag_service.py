from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import traceback
import glob

# Configuration
MODEL_NAME = "llama3.2:latest"
TEMPERATURE = 0.5
EMBEDDING_MODEL = "snowflake-arctic-embed2"
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 256
ZH_CHUNK_SIZE = 768
ZH_CHUNK_OVERLAP = 192

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
            
            # Add metadata to each page
            processed_docs = []
            for doc in documents:
                # Skip empty pages
                if not doc.page_content.strip():
                    continue
                    
                # Skip pages that only contain common headers/footers
                if len(doc.page_content.split()) < 10:
                    continue
                    
                # Add metadata
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
        """Split documents into chunks based on language with improved handling"""
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
            
            # Split and combine results with error handling
            result_docs = []
            if en_docs:
                en_chunks = en_splitter.split_documents(en_docs)
                print(f"English chunks created: {len(en_chunks)}")
                result_docs.extend(en_chunks)
            if zh_docs:
                zh_chunks = zh_splitter.split_documents(zh_docs)
                print(f"Chinese chunks created: {len(zh_chunks)}")
                result_docs.extend(zh_chunks)
            if other_docs:
                other_chunks = en_splitter.split_documents(other_docs)
                print(f"Other language chunks created: {len(other_chunks)}")
                result_docs.extend(other_chunks)
            
            print(f"Total chunks created: {len(result_docs)}")
            return result_docs
        except Exception as e:
            error_msg = f"Error splitting documents: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

    def setup_rag(self):
        """Initialize the RAG system"""
        # Initialize embeddings
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        # Load or create vector store
        vector_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vector_db')
        
        try:
            print("Loading vector store...")
            # Clear existing collection if it exists
            if os.path.exists(vector_db_path):
                print("Clearing existing vector store...")
                Chroma(persist_directory=vector_db_path, embedding_function=embeddings).delete_collection()
            
            # Create new empty vector store
            self.vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
            print("Vector store initialized")
        except Exception as e:
            print(f"Error initializing vector store: {str(e)}")
            print(traceback.format_exc())
            raise

        # Initialize LLM with specific parameters for better comprehension
        llm = ChatOllama(
            temperature=TEMPERATURE,
            model=MODEL_NAME,
            top_k=10,  # Increase number of tokens considered
            top_p=0.9,  # Slightly more focused sampling
            repeat_penalty=1.1  # Slight penalty for repetition
        )
        
        # Setup retriever with MMR search
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",  # Use MMR for better diversity
            search_kwargs={
                "k": 8,  # Increased number of retrieved documents
                "fetch_k": 30,  # Consider more candidates
                "lambda_mult": 0.9  # Strong focus on relevance to current query
            }
        )
        
        # Setup question condenser with improved prompt
        condense_template = """Given the chat history and the latest user question, create a standalone question.
        IMPORTANT: Each question should be treated independently, even if similar topics were discussed before.
        DO NOT reference previous questions or indicate that a topic has been discussed before.
        
        The standalone question should:
        1. Focus ONLY on the current question
        2. Be specific and detailed
        3. Focus on extracting factual information
        4. NEVER mention or reference previous questions
        5. NEVER use phrases like "again", "as mentioned", or similar
        
        Chat History: {chat_history}
        Latest Question: {input}
        
        Standalone question:"""

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
            ("system", """You are a helpful and friendly AI assistant capable of both general conversation and document analysis.

                    When responding to general queries:
                    - Be natural but professional
                    - Draw from your general knowledge
                    - Provide clear, complete answers
                    - End responses definitively without asking questions
                    - Avoid phrases like "Does that make sense?" or "Does that help?"

                    When the query is specifically about the documents in the context:
                    1. Carefully analyze the provided document chunks
                    2. Extract key information and main ideas
                    3. Synthesize a clear and accurate response
                    4. Focus on academic and technical details when present
                    5. End with a clear conclusion, not a question
                    
                    Document Context (only use when query is about documents):
                    {context}"""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        
        zh_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一個專業且樂於助人的AI助理，能夠進行一般對話並分析文件。

                    當回應一般查詢時：
                    - 保持自然但專業的語氣
                    - 運用你的一般知識
                    - 提供清晰完整的答案
                    - 以明確的結論結束，不要提問
                    - 避免使用「明白嗎？」或「有幫助嗎？」等問句

                    當查詢特別針對文件內容時：
                    1. 仔細分析提供的文件片段
                    2. 提取關鍵信息和主要觀點
                    3. 綜合形成清晰準確的回答
                    4. 注重學術和技術細節
                    5. 以明確的結論結束
                    
                    文件上下文（僅在查詢與文件相關時使用）：
                    {context}"""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        # Create document chains with temperature adjustment for different types of queries
        en_document_chain = create_stuff_documents_chain(
            ChatOllama(
                temperature=0.3,  # Lower temperature for document-specific queries
                model=MODEL_NAME,
                top_k=10,
                top_p=0.9,
                repeat_penalty=1.1
            ), 
            en_prompt
        )
        zh_document_chain = create_stuff_documents_chain(
            ChatOllama(
                temperature=0.3,  # Lower temperature for document-specific queries
                model=MODEL_NAME,
                top_k=10,
                top_p=0.9,
                repeat_penalty=1.1
            ), 
            zh_prompt
        )
        
        # Create retrieval chains
        self.en_chain = create_retrieval_chain(history_aware_retriever, en_document_chain)
        self.zh_chain = create_retrieval_chain(history_aware_retriever, zh_document_chain)

    async def get_response(self, query: str, chat_history: list = None) -> str:
        """Get response from the appropriate chain based on query language with improved debugging"""
        if chat_history is None:
            chat_history = []
        
        try:
            print("\n=== Debug Information ===")
            print(f"Raw query: {repr(query)}")
            print("\nChat History:")
            for msg in chat_history:
                print(f"Role: {msg['role']}, Content: {repr(msg['content'])}")
            
            # Format chat history for LangChain
            formatted_history = []
            for msg in chat_history:
                if msg['role'] == 'user':
                    formatted_history.append(("human", msg['content']))
                elif msg['role'] == 'assistant':
                    formatted_history.append(("assistant", msg['content']))
            
            print("\nFormatted History:")
            for role, content in formatted_history:
                print(f"Role: {role}, Content: {repr(content)}")

            # Detect language and use appropriate chain
            lang = self.detect_language(query)
            chain = self.zh_chain if lang == "zh" else self.en_chain
            
            # Get and log relevant documents with detailed analysis
            print("\n=== Query Analysis ===")
            print(f"Query: {repr(query)}")
            print(f"Language detected: {lang}")
            print(f"Chat history length: {len(chat_history)} messages")
            
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 8})
            relevant_docs = retriever.get_relevant_documents(query)
            
            print("\n=== Retrieved Documents Analysis ===")
            print(f"Total documents retrieved: {len(relevant_docs)}")
            
            # Group documents by source
            docs_by_source = {}
            for doc in relevant_docs:
                source = doc.metadata.get('filename', 'unknown')
                if source not in docs_by_source:
                    docs_by_source[source] = []
                docs_by_source[source].append(doc)
            
            # Print analysis by source
            print("\n=== Document Sources ===")
            for source, docs in docs_by_source.items():
                print(f"\nSource: {source}")
                print(f"Number of chunks: {len(docs)}")
                
                # Print sample content from each chunk
                for i, doc in enumerate(docs):
                    print(f"\nChunk {i+1}:")
                    print(f"Content preview: {doc.page_content[:150]}...")
                    print(f"Metadata: {doc.metadata}")
                    if 'score' in doc.metadata:
                        print(f"Relevance score: {doc.metadata['score']:.3f}")
            
            # Get response using the chain
            print("\n=== Generating Response ===")
            response = await chain.ainvoke({
                "input": query,
                "chat_history": formatted_history,
                "context": "\n\n".join(doc.page_content for doc in relevant_docs)
            })
            
            print("\n=== Response Generated ===")
            print(f"Response length: {len(response['answer'])} characters")
            
            return response["answer"]
        except Exception as e:
            error_msg = f"Error in get_response: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

# Initialize global RAG service
rag_service = RAGService() 