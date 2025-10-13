# Docling Document Parser API

A powerful REST API for parsing PDFs and documents using [Docling](https://github.com/DS4SD/docling), with AI-powered image description capabilities via Google Gemini and OpenAI.

## Features

### Document Parsing
- **Multiple Parsing Modes**:
  - `standard` - Balanced extraction with default settings
  - `ocr` - Force OCR for scanned documents
  - `fast` - Quick processing with minimal overhead
  - `high_quality` - Maximum accuracy with enhanced image extraction

### Content Extraction
- **Text Extraction**: Structured text with labels and bounding boxes
- **Table Extraction**: Export tables as CSV, JSON, or DataFrames
- **Image Extraction**: Extract images with configurable scaling (1x-4x)
- **Page Metadata**: Dimensions, page numbers, and layout information

### AI-Powered Image Descriptions
- **Docling SmolVLM**: Built-in vision model for image understanding
- **Google Gemini**: Integration with Gemini 2.5 Flash for detailed descriptions
- **OpenAI GPT-4o**: Alternative vision model support
- **Custom Prompts**: Configure description style and detail level

### API Features
- **Async Processing**: Background job processing with status tracking
- **Export Formats**: Markdown, JSON, and raw image exports
- **Progress Tracking**: Real-time job status and progress updates
- **File Validation**: Size limits, MIME type checking, and extension validation

## Tech Stack

- **Framework**: FastAPI (async REST API)
- **Document Processing**: Docling (IBM Research)
- **AI Vision**: Google Generative AI SDK, LangChain OpenAI
- **Image Processing**: PIL (Pillow)
- **Environment**: Python 3.9+, UV package manager

## Installation

### Prerequisites
- Python 3.9 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd docling-project
```

2. **Install dependencies**
```bash
uv sync
```

3. **Configure environment variables**
```bash
# Create .env file in api/ directory
cp api/.env.example api/.env
```

Edit `api/.env` and add your API keys:
```env
# Optional: AI Image Description Providers
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
MAX_FILE_SIZE_MB=50
MAX_CONCURRENT_JOBS=5
```

4. **Run the API**
```bash
cd api
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Usage

### Quick Start

Access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Parse a PDF

```bash
# Upload and parse a document
curl -X POST "http://localhost:8000/api/v1/parse/upload" \
  -F "file=@document.pdf" \
  -F "parsing_mode=standard" \
  -F "extract_images=true" \
  -F "describe_images=true" \
  -F "description_provider=gemini"

# Response includes job_id
{
  "job_id": "abc-123-def",
  "status": "processing",
  "message": "Document uploaded successfully"
}

# Check job status
curl "http://localhost:8000/api/v1/parse/jobs/abc-123-def/status"

# Get results
curl "http://localhost:8000/api/v1/parse/results/abc-123-def"
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/parse/upload` | POST | Upload and parse document |
| `/api/v1/parse/jobs/{job_id}/status` | GET | Check job status |
| `/api/v1/parse/results/{job_id}` | GET | Get parsing results |
| `/api/v1/parse/results/{job_id}/export/markdown` | GET | Export as Markdown |
| `/api/v1/parse/results/{job_id}/export/json` | GET | Export as JSON |
| `/api/v1/parse/results/{job_id}/images/{image_id}` | GET | Get extracted image |

## Project Structure

```
docling-project/
├── api/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic data models
│   ├── parser.py            # Document parsing logic
│   ├── utils.py             # Utility functions (file handling, AI descriptions)
│   ├── storage.py           # In-memory job storage
│   ├── .env                 # Environment variables (create this)
│   └── temp/                # Temporary file storage
├── docs/
│   ├── AGENTIC_ARCHITECTURE.md      # Guide for MCP + LangGraph integration
│   └── POTENTIAL_IMPROVEMENTS.md    # Feature roadmap and enhancements
├── examples/                # Example scripts and demos
├── pyproject.toml          # Project dependencies (UV)
└── README.md              # This file
```

## Configuration

Key settings in `api/config.py`:

- **File Upload**: `MAX_FILE_SIZE_MB` (default: 50MB)
- **Parsing**: `DEFAULT_PARSING_MODE`, `DEFAULT_IMAGE_SCALE`
- **Image Descriptions**: `DEFAULT_DESCRIPTION_PROMPT`, `GEMINI_MODEL`
- **Jobs**: `JOB_TIMEOUT_SECONDS`, `MAX_CONCURRENT_JOBS`
- **Storage**: `RESULTS_TTL_SECONDS` (result cache lifetime)

## Supported File Types

- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- HTML (`.html`)
- Markdown (`.md`)
- Images (`.png`, `.jpg`, `.tiff`)

## Response Structure

The API returns structured data with:
- **Metadata**: Filename, page count, processing time, file hash
- **Statistics**: Counts of text items, tables, pictures
- **Content**:
  - Markdown export of full document
  - Page-by-page information
  - Text items with labels and positions
  - Tables with CSV/JSON exports
  - Pictures with optional AI descriptions
- **Exports**: URLs for downloading results in different formats

## Future Enhancements

See [docs/POTENTIAL_IMPROVEMENTS.md](docs/POTENTIAL_IMPROVEMENTS.md) for the full feature roadmap, including:

- Document Q&A with RAG
- Multi-document batch processing
- Advanced table extraction
- Form field detection
- Document comparison
- Vector database integration

## Agentic Integration

For building agent-based applications with this API, see [docs/AGENTIC_ARCHITECTURE.md](docs/AGENTIC_ARCHITECTURE.md) for:

- FastAPI-MCP server setup
- LangGraph integration patterns
- File upload strategies for agents
- Multi-agent orchestration examples

## Credits

Built with:
- [Docling](https://github.com/DS4SD/docling) by IBM Research
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Generative AI](https://ai.google.dev/)
- [LangChain](https://www.langchain.com/)
