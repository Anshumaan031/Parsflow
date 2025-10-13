"""
Configuration for RAG examples
Centralized settings for all RAG scripts
"""
import os
from pathlib import Path

# API Configuration
API_BASE_URL = os.getenv("DOCLING_API_URL", "http://localhost:8000")
API_TIMEOUT = 300  # seconds

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️  Warning: OPENAI_API_KEY environment variable not set")

# Model Configuration
TEXT_MODEL = "gpt-4o-mini"  # Cheaper for text-only
VISION_MODEL = "gpt-4o"  # Required for image understanding
EMBEDDING_MODEL = "text-embedding-3-small"  # For vector embeddings

# Parsing Configuration
DEFAULT_PARSING_MODE = "standard"  # standard, ocr, fast, high_quality
HIGH_QUALITY_PARSING_MODE = "high_quality"
DEFAULT_IMAGE_SCALE = 2.0
HIGH_QUALITY_IMAGE_SCALE = 3.0

# RAG Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
TOP_K_RESULTS = 4  # Number of results to retrieve

# Vector Store Configuration
VECTOR_STORE_TYPE = "faiss"  # faiss or chroma
VECTOR_STORE_PATH = Path("./vector_stores")

# Output Configuration
OUTPUT_DIR = Path("./rag_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Processing Configuration
MAX_IMAGES_TO_PROCESS = None  # None = all images, or set a limit
SKIP_DECORATIVE_IMAGES = True  # Try to skip decorative images
MIN_IMAGE_SIZE = 50  # Minimum size in pixels

# Polling Configuration
POLL_INTERVAL = 2  # Seconds between status checks
MAX_POLL_TIME = 600  # Maximum time to wait for processing

# Display Configuration
VERBOSE = True
SHOW_PROGRESS = True
TRUNCATE_DISPLAY = 150  # Characters to show in console output

# Temperature settings
QA_TEMPERATURE = 0  # Lower for factual answers
CREATIVE_TEMPERATURE = 0.3  # Higher for creative responses
