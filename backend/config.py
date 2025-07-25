from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

# Load environment variables from a .env file (e.g., for API keys)
load_dotenv()

# Retrieve the API key explicitly
google_api_key = os.getenv("GOOGLE_API_KEY")

# Initialize the Google Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0.0,
    google_api_key=google_api_key)

# Define paths to your persisted ChromaDB directories
CHROMA_PATH_EN = r"backend\chroma_db_archive_en"
CHROMA_PATH_AR = r"backend\chroma_db_archive_ar"

# Initialize the embedding function
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# Initialize the ChromaDB instance for English
en_db = None
try:
    en_db = Chroma(persist_directory=CHROMA_PATH_EN, embedding_function=embedding_function)
except Exception as e:
    pass

# Initialize the ChromaDB instance for Arabic
ar_db = None
try:
    ar_db = Chroma(persist_directory=CHROMA_PATH_AR, embedding_function=embedding_function)
except Exception as e:
    pass
    
# Initialize retrievers
en_retriever = None
if en_db:
    en_retriever = en_db.as_retriever(search_kwargs={"k": 3})
else:
    pass

ar_retriever = None
if ar_db:
    ar_retriever = ar_db.as_retriever(search_kwargs={"k": 3})
else:
    pass


retrievers_by_lang = {
    "en": en_retriever,
    "ar": ar_retriever
}