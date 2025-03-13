# main.py
import gradio as gr
from loaders import load_documents, split_documents
from vectorstore import create_vectorstore
from chatbot import setup_chatbot, detect_query_language
from langchain_core.messages import HumanMessage, AIMessage

def main():
    print("Starting RAG application...")
    
    # Load and process documents
    print("Loading documents...")
    documents = load_documents()
    
    print("Splitting documents into chunks...")
    chunks = split_documents(documents)
    # print(f"Total chunks: {len(chunks)}")
    
    print("Creating vector store...")
    vectorstore = create_vectorstore(chunks)
    
    print("Setting up multilingual chatbot...")
    chains, vectorstore_for_search = setup_chatbot(vectorstore)
    print("RAG system ready!")
    
    # Initialize chat history
    chat_history = []
    
    def chat(question, history):
        # Detect language
        lang = detect_query_language(question)
        print(f"Detected language: {lang}")
        
        # Format history for LangChain
        formatted_history = []
        for human_msg, ai_msg in history:
            formatted_history.append(HumanMessage(content=human_msg))
            formatted_history.append(AIMessage(content=ai_msg))
        
        if lang == "zh":
            chain = chains["zh_retrieval"]
        else:
            chain = chains["en_retrieval"]

        result = chain.invoke({
            "input": question,
            "chat_history": formatted_history
        })
        print(result)
        # Update the chat history (for the next iteration)
        chat_history.append((question, result))
        
        return result["answer"] if isinstance(result, dict) else str(result)
        
    # Create Gradio interface
    gr.ChatInterface(
        chat, 
        title="Multilingual Document Assistant",
        description="Ask questions in English or Chinese about your documents"
    ).launch(inbrowser=True)


if __name__ == "__main__":
    main()