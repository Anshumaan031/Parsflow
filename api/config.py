"""
Configuration settings for Docling Parser API
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Try api/.env first, then root .env
api_env_path = Path(__file__).parent / ".env"
root_env_path = Path(__file__).parent.parent / ".env"

if api_env_path.exists():
    load_dotenv(api_env_path)
elif root_env_path.exists():
    load_dotenv(root_env_path)
else:
    load_dotenv()  # Try default search

class Settings:
    """API Configuration Settings"""

    # API Settings
    API_TITLE: str = "Docling Document Parser API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "REST API for parsing PDFs and documents using Docling"

    # Server Settings
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".html", ".md"]

    # Supported MIME types
    SUPPORTED_MIME_TYPES: dict = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
        'text/html': 'html',
        'text/markdown': 'markdown',
        'image/png': 'image',
        'image/jpeg': 'image',
        'image/tiff': 'image'
    }

    # Storage Settings
    TEMP_DIR: Path = Path("api/temp")
    OUTPUT_DIR: Path = Path("api/output")
    RESULTS_TTL_SECONDS: int = 3600  # 1 hour

    # Job Settings
    JOB_TIMEOUT_SECONDS: int = 300  # 5 minutes
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

    # Parsing Settings
    DEFAULT_PARSING_MODE: str = "standard"
    DEFAULT_IMAGE_SCALE: float = 2.0
    DEFAULT_EXTRACT_IMAGES: bool = True
    DEFAULT_EXTRACT_TABLES: bool = True

    # Image Description Settings
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_DESCRIPTION_PROMPT: str = "Describe this image in detail. Include what type of visual it is (chart, diagram, photo, etc.), main content, any text visible, and key insights."
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"  # Gemini model for image descriptions

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute

    def __init__(self):
        """Create necessary directories on initialization"""
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
