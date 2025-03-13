# chatbot.py
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import re
from config import MODEL_NAME, TEMPERATURE

def detect_query_language(query):
    """Detect if query is primarily in Chinese"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', query))
    if chinese_chars > len(query) * 0.2:  # If more than 20% Chinese characters
        return "zh"
    return "en"


def setup_chatbot(vectorstore, model=MODEL_NAME, temperature=TEMPERATURE):
    # Initialize LLM
    llm = ChatOllama(temperature=temperature, model=model)
    
    # Initialize retriever with appropriate number of documents, k can be adjusted
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
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
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever=retriever, prompt=condense_question_prompt
    )

    # English prompt template for document chain
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
    
    # Chinese prompt template for document chain
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
    
    # Create document chains for each language
    en_document_chain = create_stuff_documents_chain(llm, en_prompt)
    zh_document_chain = create_stuff_documents_chain(llm, zh_prompt)
    
    # Create retrieval chains using the create_retrieval_chain method
    en_retrieval_chain = create_retrieval_chain(history_aware_retriever, en_document_chain)
    zh_retrieval_chain = create_retrieval_chain(history_aware_retriever, zh_document_chain)
    
    
    # Return all chains along with vectorstore
    return {
        "en_retrieval": en_retrieval_chain,
        "zh_retrieval": zh_retrieval_chain,
    }, vectorstore