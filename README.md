# Local Content Certificate Identifier 🏭📋

An intelligent, multi-language agent designed to analyze product lists and determine Local Content Certificate requirements. Powered by **LangGraph** and **Google Gemini**, this application provides conversational insights into mandatory product listings with persistent conversation history and bilingual document retrieval.

-----

## 🖼️ Application UI

The app features a clean, interactive chat interface where users can input products (text or file), view analysis results, and interact with the AI agent to get detailed certificate requirements and compliance information.

![Local Content Certificate Application](Local%20Content%20Certificate%20Identifier%20App.png)

-----

## ✨ Overview

**Local Content Certificate Identifier** streamlines the product compliance verification process. Instead of manually searching through extensive regulatory documents, users can input product names or upload product lists and query an intelligent agent to quickly determine:

- Whether products are listed in mandatory certification lists
- If Local Content Certificates are required
- Detailed reasoning for each determination
- Bilingual support for Arabic and English products

The app architecture leverages:

- **LangGraph** for stateful, multi-step analytical workflows
- **FastAPI** for robust backend API with file upload support
- **ChromaDB** for efficient vector-based document retrieval
- **SQLite** for persistent conversation history and checkpointing
- **Google Gemini 2.5 Pro** for intelligent product analysis and natural language understanding
- **HuggingFace Embeddings** for multilingual semantic search

-----

## ⚙️ How It Works

The agent follows a sophisticated LangGraph flow to process product queries and provide certificate requirements:

1. **Input Processing**: Users input product names via text or upload Excel/text files. The system supports both Arabic and English product names.

2. **Language Detection & Parsing**: The `parse_input` node uses an LLM to extract individual product names and detect their language (Arabic or English).

3. **Document Retrieval**: The `retrieve_documents_for_items` node queries the appropriate language-specific ChromaDB vector store to find relevant regulatory documents.

4. **Product Analysis**: The `analyze_product_match` node determines:
   - If each product is listed in the mandatory certification list
   - Whether a Local Content Certificate is required
   - Provides detailed reasoning for each decision

5. **Response Generation**: The `prepare_final_output` node synthesizes all analyses into a comprehensive, user-friendly report.

6. **Conversation Persistence**: All interactions are stored with LangGraph checkpoints, ensuring seamless conversation continuity.

-----

## 🧠 Graph Architecture

The architecture uses a linear LangGraph workflow optimized for product compliance analysis. Each node performs a specific function in the analysis pipeline, ensuring accurate and thorough evaluation of product requirements.

![Local Content Certificate Graph](Local%20Content%20Certificate%20Identifier%20Graph.png)

**Graph Flow:**
```
Parse Input → Retrieve Documents → Analyze Products → Prepare Final Output
```

-----

## 🚀 Key Features

- **Intelligent Product Analysis**: Automatically determines listing status and certificate requirements for products
- **Bilingual Support**: Handles both Arabic and English product names with language-specific document retrieval
- **File Upload Support**: Process Excel (.xlsx, .xls) and text (.txt) files containing product lists
- **Persistent Chat Memory**: All conversations saved in SQLite database with LangGraph checkpointing
- **Vector-Based Search**: Uses ChromaDB for efficient semantic search across regulatory documents
- **Structured Output**: Provides clear reasoning for each product determination
- **Real-time Processing**: Interactive chat interface with typing indicators and file upload feedback
- **Conversation Management**: Clear history functionality and session persistence

-----

## 🛠️ Tech Stack

- **Orchestration**: LangChain & LangGraph
- **LLM**: Google Gemini (`gemini-2.5-pro`)
- **Vector Database**: ChromaDB with HuggingFace embeddings
- **Backend API**: FastAPI with file upload support
- **Frontend**: HTML/CSS/JavaScript with modern chat UI
- **Database**: SQLite for conversation persistence
- **Embeddings**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- **Environment Management**: Python `venv` or `Docker`

-----

## 📦 Setup & Installation

### Data Preparation (One-time setup)

First, prepare your regulatory data using the preprocessing notebook and then:

### Option 1: Run Locally (venv)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/eslammohamedtolba/Multilingual-Product-Compliance-Agent.git
   cd Multilingual-Product-Compliance-Agent
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   # Create the environment
   python -m venv venv

   # Activate on Windows
   venv\Scripts\activate

   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
   ```

5. **Launch the Application**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

6. **Access the App**
   Open `http://localhost:8000` in your browser and start analyzing your products!

-----

### Option 2: Run with Docker

1. **Ensure Docker is Running**

2. **Build the Docker Image**
   ```bash
   docker build -t local-content-cert-app .
   ```

3. **Run the Container**
   ```bash
   docker run -p 8000:8000 \
     -v "$(pwd)/backend/db.sqlite:/app/backend/db.sqlite" \
     -v "$(pwd)/backend/chroma_db_archive_en:/app/backend/chroma_db_archive_en" \
     -v "$(pwd)/backend/chroma_db_archive_ar:/app/backend/chroma_db_archive_ar" \
     -v "$(pwd)/uploads:/app/uploads" \
     -v "$(pwd)/.env:/app/.env" \
     --name local-content-cert-container \
     local-content-cert-app
   ```

   **Explanation:**
   - `-p 8000:8000`: Maps FastAPI's port to your host machine
   - `-v ...`: Mounts local directories for data persistence
   - `--name`: Assigns a readable name to the container

4. **Access the Application**
   Go to: `http://localhost:8000`

5. **Stop the Container**
   ```bash
   docker stop local-content-cert-container
   ```

-----

## 📚 Usage Examples

### Text Input
```
"laptop computers and desktop monitors"
```

### File Upload
Upload Excel files containing product lists:
- Column structure: Product names in Arabic and English
- Supports .xlsx, .xls, and .txt formats

### API Endpoints
- `GET /`: Main chat interface
- `POST /api/send_message`: Send product queries
- `GET /api/history`: Retrieve chat history  
- `POST /api/clear_history`: Clear conversation history

-----

## 🔧 Configuration

### Environment Variables
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### ChromaDB Paths
- English documents: `backend/chroma_db_archive_en`
- Arabic documents: `backend/chroma_db_archive_ar`

### Database
- SQLite database: `backend/db.sqlite`
- Stores conversation history and LangGraph checkpoints

-----

## 🤝 Contributing

We welcome contributions! Feel free to:
- Fork this repository
- Open issues for bugs or feature requests
- Submit pull requests to enhance functionality
- Improve documentation or add new analytical tools
- Optimize performance or add new language support
