from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import traceback
import shutil
import base64
from openai import OpenAI
from dotenv import load_dotenv
import uuid
import requests
from bs4 import BeautifulSoup
import trafilatura

# Configuration - Exactly matching reference implementation
MODEL_NAME = "llama3.2:latest"
# MODEL_NAME = "gemma3:4b"
# MODEL_NAME = "qwen2.5:3b"
TEMPERATURE = 0.5
EMBEDDING_MODEL = "snowflake-arctic-embed2"
# EMBEDDING_MODEL = "bge-m3:latest"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
CHUNK_SIZE_L = 1024
CHUNK_OVERLAP_L = 100
# ZH_CHUNK_SIZE_L = 384
# ZH_CHUNK_OVERLAP_L = 75
ZH_CHUNK_SIZE = 200
ZH_CHUNK_OVERLAP = 30

load_dotenv()

# System messages for web search
SEARCH_OR_NOT_MSG = (
    'Return True if the user is asking about current events, news, or facts that require up-to-date '
    'information. Return False if the question can be answered without searching. Respond only with '
    '"True" or "False".'
)

QUERY_MSG = (
    'Create a simple search query to find the specific information needed. Use only essential keywords and dates. '
    'No special operators or formatting. Focus on the core question without adding assumptions. '
    'For current events or facts, include "current" . '
    'Examples: "current us president" or "tesla stock price today" or "weather new york". '
    'Keep it under 5 words when possible. Do not include names of people unless specifically asked about them.'
)

CONTAINS_DATA_MSG = (
    'Check if this webpage contains information that could help answer the user\'s question. '
    'Return True if the page contains:\n'
    '1. Direct answers to the question\n'
    '2. Recent information about the topic\n'
    '3. Background context that helps understand the answer\n'
    '4. Related facts or figures that could be relevant\n'
    'Only return False if the page is completely unrelated or contains no useful information. '
    'Respond only with "True" or "False" - no other text.'
)

WEB_SEARCH_RESPONSE_TEMPLATE = """WEB SEARCH RESULTS:
{search_results}

USER QUERY: {query}

Based on the web search results above, provide a comprehensive, accurate answer to the user's query.
Include only information found in the search results.
You must provide an objective answer based on the search results, don't say you don't have enough information.
The answer should be unambiguous, don't say "it appears that" or "it may be".
The answer should be a paragraph of 4 or 5 sentences.
You don't have to cite the sources.
If the search results contain conflicting information, prioritize the most recent and authoritative sources.
For questions about current events or facts, ensure the information is up-to-date and accurate.
"""

class RAGService:
    def __init__(self):
        self.vectorstores = {}  # Dictionary to store vectorstores by conversation_id
        self.chains = {}  # Dictionary to store chains by conversation_id
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.base_vector_path = os.path.join(os.path.dirname(__file__), '..', '..', 'vector_db')
        self.openai_client = OpenAI()
        self.images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
        os.makedirs(self.images_dir, exist_ok=True)
        
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
            # en_splitter = RecursiveCharacterTextSplitter(
            #         chunk_size=CHUNK_SIZE,
            #         chunk_overlap=CHUNK_OVERLAP,
            #         separators=["\n\n", "\n", ". ", " ", ""]
            #     )
            zh_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=ZH_CHUNK_SIZE,
                    chunk_overlap=ZH_CHUNK_OVERLAP,
                    separators=["\n\n", "\n", "。", "，", "、", " ", ""]
                )
            # Configure language-specific splitters
            if (len(en_docs) > 10):
                en_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE_L,
                    chunk_overlap=CHUNK_OVERLAP_L,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
            else:
                en_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
            
            # if (len(zh_docs) > 10):
            #     zh_splitter = RecursiveCharacterTextSplitter(
            #         chunk_size=ZH_CHUNK_SIZE_L,
            #         chunk_overlap=ZH_CHUNK_OVERLAP_L,
            #         separators=["\n\n", "\n", "。", "，", "、", " ", ""]
            #     )
            # else:   
            #     zh_splitter = RecursiveCharacterTextSplitter(
            #         chunk_size=ZH_CHUNK_SIZE,
            #         chunk_overlap=ZH_CHUNK_OVERLAP,
            #         separators=["\n\n", "\n", "。", "，", "、", " ", ""]
            #     )
            
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
            retriever = self.vectorstores[conversation_id].as_retriever(search_kwargs={"k": 5})
            
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
                ("system", """You are a helpful and friendly AI assistant capable of general conversation, document analysis, image generation, and web search.

                        Core principles:
                        1. Never make up information or statistics
                        2. If you don't know something, simply say so in a polite way
                        3. Be consistent with previous responses
                        4. If correcting a previous response, acknowledge the correction
                        5. Clearly distinguish between document-based and general knowledge
                        6. Maintain accurate awareness of the conversation history
                        7. When summarizing conversations, only include topics that were actually discussed
                        8. When summarizing chat history, if the web search result conflicts with the llm knowledge, prioritize the web search result
                        9. Don't make assumptions about previous conversations or topics

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
                           - When asked about conversation history, only include topics that were explicitly discussed
                           - Don't make up or assume topics that weren't part of the conversation

                        4. For image generation context:
                           - Acknowledge when users are thanking you for generated images
                           - Maintain awareness of image-related context in the conversation
                           - Offer relevant follow-up suggestions about image adjustments or new generations
                           - Don't deny or contradict previous image generation actions

                        5. For web search context:
                           - When responding based on web search results, synthesize the information clearly
                           - Maintain awareness of web search context in the conversation's chat history
                           - Cite sources when appropriate by mentioning the website or publication
                           - Acknowledge the recency of information when responding to questions about current events
                           - Don't deny or contradict the fact that web search was used to find information
                        
                        \n\n
                        {context}"""),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
            ])
            
            zh_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一個專業且親切的AI助理，能夠進行一般對話、分析文件、圖片生成和網絡搜索。

                        核心原則：
                        1. 絕不編造資訊或統計數據
                        2. 請使用繁體中文進行回答，不要參雜其他語言，除非是文件中出現的專有名詞
                        3. 如果不知道答案，請禮貌的說不知道
                        4. 保持回答的一致性
                        5. 如果需要更正先前的回答，要明確說明
                        6. 清楚區分文件內容和一般知識
                        7. 保持對對話歷史的準確認知
                        8. 總結對話時，只包含實際討論過的主題
                        9. 總結對話紀錄時，如果網絡搜索結果和LLM原有知識起衝突，優先使用網絡搜索結果
                        10. 不要對之前的對話或主題做出假設

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
                           - 當被詢問對話歷史時，只包含明確討論過的主題
                           - 不要編造或假設未在對話中出現的主題

                        4. 針對圖片生成相關對話：
                           - 當用戶感謝你生成的圖片時，要適當回應
                           - 保持對圖片相關上下文的認知
                           - 提供相關的後續建議，如調整圖片或生成新的圖片
                           - 不要否認或矛盾之前的圖片生成行為

                        5. 針對網絡搜索相關對話：
                           - 當回應基於網絡搜索結果時，要清晰地綜合信息
                           - 在對話中保持對網絡搜索上下文的認知
                           - 在適當的時候引用來源，例如提及網站或出版物
                           - 在回答關於時事的問題時，確認信息的時效性
                           - 不要否認或矛盾網絡搜索被用來查找信息的事實
                        
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

    async def query_generator(self, query):
        """Generate a search query based on user input"""
        try:
            llm = ChatOllama(
                temperature=0.1,  # Explicitly set low temperature for more deterministic results
                model=MODEL_NAME
            )
            
            # Use the exact format from search_agent.py
            query_msg = f'CREATE A SEARCH QUERY FOR THIS PROMPT: \n{query}'
            
            # Format messages exactly like in search_agent.py
            response = await llm.ainvoke([
                {"role": "system", "content": QUERY_MSG},
                {"role": "user", "content": query_msg}
            ])
            
            # Clean up the query string according to search_agent.py pattern
            search_query = response.content.strip()
            # Remove quotes if they exist at the start and end
            search_query = search_query.strip('"\'')
            # Remove any newlines and extra spaces
            search_query = ' '.join(search_query.split())
            
            # # Apply additional filtering to remove unnecessary terms
            # words = search_query.split()
            # if len(words) > 6:  # Keep it concise as per the system message
            #     search_query = ' '.join(words[:6])
            
            print(f"Generated search query: {search_query}")
            return search_query
        except Exception as e:
            print(f"Error generating search query: {str(e)}")
            # Fall back to a very simple query based on the original
            simple_query = ' '.join(query.split()[:4])  # Just take first few words
            return simple_query

    async def duckduckgo_search(self, query):
        """Search DuckDuckGo for the query"""
        print(f"Searching DuckDuckGo for: {query}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            }
            url = f'https://html.duckduckgo.com/html/?q={query}'
            
            # Use a timeout to avoid hanging
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
                if i > 5:  # Limit to top 5 results
                    break

                title_tag = result.find('a', class_='result__a')
                if not title_tag:
                    continue

                link = title_tag['href']
                snippet_tag = result.find('a', class_='result__snippet')
                snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'

                results.append({
                    'id': i,
                    'link': link,
                    'search_description': snippet
                })
                print(f"Found result #{i}: {link[:100]}...")

            print(f"Total results found: {len(results)}")
            return results
        except Exception as e:
            print(f"Error searching DuckDuckGo: {str(e)}")
            return []

    async def scrape_webpage(self, url):
        """Scrape content from a webpage with timeout"""
        print(f"Attempting to scrape webpage: {url}")
        try:
            print("Downloading webpage content...")
            # Use a shorter timeout for download
            downloaded = trafilatura.fetch_url(url=url)
            if downloaded:
                print("Successfully downloaded webpage")
                content = trafilatura.extract(downloaded, include_formatting=True, include_links=True)
                if content:
                    if len(content) > 8000:  # Shorter content limit to avoid LLM context issues
                        content = content[:8000]
                        print("Truncated content")
                    print(f"Successfully extracted content (length: {len(content)} characters)")
                    return content
                else:
                    print("Failed to extract content from webpage")
                    return None
            else:
                print("Failed to download webpage")
                return None
        except Exception as e:
            print(f"Error scraping webpage: {str(e)}")
            return None

    async def contains_data_needed(self, search_content, query, user_query):
        """Check if the search content contains relevant data for the query"""
        try:
            llm = ChatOllama(
                temperature=0.1,
                model=MODEL_NAME
            )
            
            # Truncate content to ensure LLM can process it
            if len(search_content) > 5000:
                search_content = search_content[:5000] + "..."
            
            needed_prompt = f'PAGE_TEXT: {search_content} \nUSER_PROMPT: {user_query} \nSEARCH_QUERY: {query}'
            
            response = await llm.ainvoke([
                {"role": "system", "content": CONTAINS_DATA_MSG},
                {"role": "user", "content": needed_prompt}
            ])
            
            content = response.content.lower()
            
            if 'true' in content:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error checking if content contains data: {str(e)}")
            # Default to True if there's an error, to be more inclusive
            return True

    async def web_search(self, query):
        """Perform web search and return relevant content"""
        try:
            print('GENERATING SEARCH QUERY.')
            # Generate search query
            search_query = await self.query_generator(query)
            if not search_query:
                print("Failed to generate search query")
                return None
                
            # Search DuckDuckGo
            search_results = await self.duckduckgo_search(search_query)
            if not search_results:
                print("No search results found")
                return None
                
            contexts = []
            checked_urls = set()
            max_sources = 5  # Increased to get more sources for better accuracy
            
            # Process results in order
            for result in search_results:
                if len(contexts) >= max_sources:
                    break
                    
                url = result['link']
                if url in checked_urls:
                    continue
                    
                checked_urls.add(url)
                print(f"\nChecking source {len(contexts) + 1} of {max_sources}: {url}")
                
                # Skip certain domains that might have outdated information
                # if any(domain in url.lower() for domain in ['wikipedia.org', 'archive.org']):
                #     continue
                
                page_text = await self.scrape_webpage(url)
                if not page_text:
                    continue
                    
                # Skip relevance check for the first source to ensure we get at least one result
                if len(contexts) == 0 or await self.contains_data_needed(page_text, search_query, query):
                    print("Source contains relevant information - adding to context")
                    # Add timestamp if available in the page
                    contexts.append(f"Source: {url}\n\n{page_text}")
                else:
                    print("Source does not contain relevant information - skipping")
            
            if contexts:
                print(f'\nFound {len(contexts)} relevant sources')
                return '\n\n---\n\n'.join(contexts)
            else:
                print('\nNo relevant sources found')
                return None
                
        except Exception as e:
            print(f"Error in web_search: {type(e).__name__}: {str(e)}")
            return None

    async def generate_image(self, prompt: str) -> str:
        """Generate an image using DALL-E"""
        try:
            # Generate image using DALL-E
            response = self.openai_client.images.generate(
                model="dall-e-2",
                prompt=prompt,
                size="256x256",
                n=1,
                response_format="b64_json"
            )
            
            # Get the base64 image data
            image_data = response.data[0].b64_json
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.png"
            
            # Save the image to the static directory
            image_path = os.path.join(self.images_dir, filename)
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            # Return the URL path
            return f"/static/images/{filename}"
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            print(traceback.format_exc())
            raise

    async def get_response(self, conversation_id: str, query: str, chat_history: list = None, is_image_generation: bool = False, is_web_search: bool = False) -> str:
        """Get response from the appropriate chain based on query language or generate image"""
        if chat_history is None:
            chat_history = []
        
        try:
            # Handle image generation
            if is_image_generation:
                image_url = await self.generate_image(query)
                # Create a more natural response for image generation
                response = f"""I've generated an image based on your prompt: "{query}"

                <img src="{image_url}" alt="Generated image" class="generated-image" />

                Feel free to let me know if you'd like any adjustments to the image or if you'd like to generate another one with different parameters!"""
                return response
            
            # Initialize RAG for this conversation if not already done
            if conversation_id not in self.chains:
                self.setup_rag(conversation_id)
            
            # Format chat history using langchain Message objects
            formatted_history = []
            for msg in chat_history:
                if msg['role'] == 'user':
                    formatted_history.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    formatted_history.append(AIMessage(content=msg['content']))

            # Detect language and use appropriate chain
            lang = self.detect_language(query)
            chain = self.chains[conversation_id]["zh" if lang == "zh" else "en"]
            
            # Handle web search
            if is_web_search:
                # Perform web search with timeout
                search_results = await self.web_search(query)
                
                if search_results:
                    # Extract source URLs for citation
                    sources = []
                    for result in search_results.split("Source: "):
                        if result.strip():
                            url_end = result.find("\n")
                            if url_end > 0:
                                url = result[:url_end].strip()
                                if url and url not in sources and url.startswith("http"):
                                    sources.append(url)
                    
                    # Add search results to the prompt
                    prompt = WEB_SEARCH_RESPONSE_TEMPLATE.format(
                        search_results=search_results,
                        query=query
                    )
                                        
                    # Get response using the chain
                    result = await chain.ainvoke({
                        "input": prompt,
                        "chat_history": formatted_history
                    })
                    
                    # Get the response
                    response = result["answer"] if isinstance(result, dict) else str(result)
                    
                    # Format citations at the end
                    if sources:
                        response += "\n\nSources:\n"
                        for i, source in enumerate(sources, 1):
                            response += f"[{i}] {source}\n"
                else:
                    # No search results found
                    response = f"I tried searching the web for information about '{query}', but couldn't find relevant results. Would you like me to try a different search query, or can I help you with something else?"
                
                return response
            
            # Regular RAG response
            # Get response using the chain
            result = await chain.ainvoke({
                "input": query,
                "chat_history": formatted_history
            })
            
            # Get the response
            response = result["answer"] if isinstance(result, dict) else str(result)
            
            return response
        except Exception as e:
            error_msg = f"Error in get_response for conversation {conversation_id}: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)

# Initialize global RAG service
rag_service = RAGService()