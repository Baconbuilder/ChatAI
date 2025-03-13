# Bilingual Retrieval-Augmented Generation (RAG) Chatbot / Assistant 

This project implements a Retrieval-Augmented Generation (RAG) chatbot using Langchain 0.3 and Ollama for document retrieval and question answering, with Gradio providing an interactive web interface.

The chatbot leverages Llama 3.2 as the large language model (LLM) and Snowflake's Arctic Embed 2.0 as the embedding model. It is designed to load and process both English and Mandarin PDF documents, split them into retrievable chunks, and generate context-aware answers in either language.

## How to Run

### Requirements

This project is built with Python 3.11.11. You can create a Conda environment using:

```
conda create -n rag_chatbot python=3.11.11
conda activate rag_chatbot
```

To install dependencies, run:

```
pip install -r requirements.txt
```

The full list of dependencies is provided in the `requirements.txt` file.

Additionally, pull the required Ollama models:

```
ollama pull llama3.2
ollama pull snowflake-arctic-embed2
```

### Preparing Documents

Place your PDF documents inside the `Root` folder. You can organize the PDFs into multiple subfolders or place them all in a single folder inside `Root`. The structure can look like this:

```
Root/
├── Category1/
│   └── document1.pdf
├── Category2/
│   └── document2.pdf
└── ...
```
Or this
```
Root/
└── YourDocuments/
    ├── document1.pdf
    ├── document2.pdf
    └── ...
```

The script will load all PDFs from the `Root` directory, split them into chunks, and store their embeddings in a Chroma vector database for retrieval.

### Running the Chatbot

Start the chatbot using:

```
python main.py
```

The Gradio interface will launch in your default browser, allowing you to chat with the RAG-powered assistant.

## Project Structure

```
├── Root/                 # Folder containing PDF documents
│   └── YourDocuments/
│       ├── document1.pdf
│       ├── document2.pdf
│       └── ...
├── loaders.py            # Loads and splits PDF documents
├── vectorstore.py        # Manages vector storage using Chroma and Ollama embeddings
├── chatbot.py            # Handles chatbot logic and RAG setup
├── config.py             # Configuration file for constants
├── main.py               # Main entry point with Gradio interface
├── requirements.txt      
└── README.md             
```

## Key Features

- **Multilingual Support:** Processes and retrieves information from English and Mandarin documents, allowing queries in both languages.
- **RAG-based QA:** Retrieve contextually relevant document chunks for accurate answers.
- **Document Ingestion:** Load and process PDF documents from structured folders.
- **Conversational Memory:** Retains chat history for smoother interactions.
- **Gradio Interface:** A clean and user-friendly web interface for interactions.

## Configuration

Adjust parameters in `config.py` as needed

