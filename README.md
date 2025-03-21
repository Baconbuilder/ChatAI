# Context-Aware AI Chat Platform

A comprehensive context-aware AI chat platform that combines multiple AI capabilities into a single, user-friendly interface. Built with FastAPI and Vue.js, this platform offers general chat, document-based RAG, image generation, and web search capabilities, all while maintaining contextual awareness across conversation history and user interactions.

## Features

### Core Capabilities
- **General Chat:** Engage in natural conversations with the AI assistant using Ollama's Llama 3.2 model
- **Document RAG:** Upload and query PDF documents with context-aware responses
- **Image Generation:** Create images using DALL-E with an intuitive interface
- **Web Search:** Real-time web search with context integration and source verification
- **Multilingual Support:** Support for multiple languages, with RAG optimization specifically for English and Mandarin
- **Conversation Management:** Create, update, and delete conversations with persistent history and automatic title generation

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **AI/ML:**
  - Ollama with Llama 3.2 for chat (supports other models from Ollama)
  - Snowflake Arctic Embed 2.0 for embeddings
  - Langchain 0.3.x for RAG implementation
  - ChromaDB for vector storage
  - DALL-E for image generation

### Frontend
- **Framework:** Vue.js 3
- **Build Tool:** Vite
- **State Management:** Vuex with modular store design
- **Routing:** Vue Router with authentication guards
- **HTTP Client:** Axios with interceptors
- **UI Components:** Custom components for chat, documents, and user interface

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints (auth, conversations, documents)
│   │   ├── core/          # Core configurations and settings
│   │   ├── db/            # Database models and session
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic (RAG, chat, image generation)
│   ├── Root/              # User document storage
│   ├── static/            # Static files (generated images)
│   └── vector_db/         # Vector database for document embeddings
│
└── frontend/
    └── src/
        ├── assets/        # Static assets and styles
        ├── components/    # Reusable Vue components
        ├── router/        # Vue Router configuration
        ├── services/      # API service modules
        ├── store/         # Vuex store modules
        ├── views/         # Page components
        └── App.vue        # Root component
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 16+
- OpenAI API key
- SQLite3
- Ollama installed and running locally

### Backend Setup

1. Create and activate a Conda environment:
```bash
conda create -n chat_ai python=3.11
conda activate chat_ai
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Pull required Ollama models:
```bash
ollama pull llama3.2
ollama pull snowflake-arctic-embed2
```

4. Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```
Copy the generated key as SECRET_KEY to use in step 5.

5. Set up environment variables in `backend/.env`:
```OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///gptinterface.db
SECRET_KEY=your_secret_key_here
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables in `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

## Running the Application

1. Start the backend server:
```bash
cd backend
conda activate chat_ai
python run.py
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Access the application at `http://localhost:5173`

## Features in Detail

### Chat Interface
- Support for general chat, document querying, image generation, and web search
- Multilingual conversation support
- Toggle buttons for switching between different modes
- Real-time updates with optimistic UI rendering

### Document Management
- PDF document upload directly from the chat interface
- Language-aware document chunking (optimized for English and Chinese)
- Context-aware document querying with relevance scoring
- Vector-based similarity search with ChromaDB

### Image Generation
- DALL-E integration for image creation
- Dedicated image generation mode in chat interface

### Web Search
- DuckDuckGo integration with smart query generation
- Content relevance verification and extraction

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
