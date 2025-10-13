# Docling Document Parser REST API

A production-ready REST API for parsing documents (PDF, DOCX, HTML, etc.) using [Docling](https://github.com/DS4SD/docling). Extracts text, tables, images, and metadata with full support for OCR.

## Features

✅ **Multiple Document Formats**: PDF, DOCX, DOC, HTML, Markdown, Images
✅ **Async Job Processing**: Non-blocking document parsing
✅ **Complete Data Extraction**: Text, tables, images, metadata
✅ **Multiple Parsing Modes**: Standard, OCR, Fast, High Quality
✅ **RESTful Design**: Clean, well-documented API endpoints
✅ **Structured Output**: JSON responses with full document structure
✅ **Export Formats**: Markdown, JSON, CSV
✅ **Interactive Docs**: Automatic Swagger/OpenAPI documentation

---

## Quick Start

### 1. Installation

```bash
cd api
pip install -r requirements.txt
```

### 2. Run the API

```bash
python main.py
```

The API will start at `http://localhost:8000`

### 3. View Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/parse/document` | Upload and parse a document |
| `GET` | `/api/v1/parse/jobs/{job_id}` | Check job status |
| `GET` | `/api/v1/parse/results/{job_id}` | Get complete results |

### Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/parse/results/{job_id}/texts` | Get text items (filterable) |
| `GET` | `/api/v1/parse/results/{job_id}/tables` | Get tables (CSV or dict) |
| `GET` | `/api/v1/parse/results/{job_id}/images` | Get images with metadata |

### Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/parse/results/{job_id}/export/markdown` | Export as Markdown |
| `GET` | `/api/v1/parse/results/{job_id}/export/json` | Export as JSON |

---

## Usage Examples

### 1. Parse a PDF Document

```bash
curl -X POST "http://localhost:8000/api/v1/parse/document" \
  -F "file=@document.pdf" \
  -F "parsing_mode=standard"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "status_url": "/api/v1/parse/jobs/550e8400-e29b-41d4-a716-446655440000",
  "estimated_time_seconds": 30
}
```

### 2. Check Job Status

```bash
curl "http://localhost:8000/api/v1/parse/jobs/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress_percent": 100,
  "result_url": "/api/v1/parse/results/550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-08T10:30:00Z",
  "completed_at": "2025-10-08T10:30:45Z"
}
```

### 3. Get Complete Results

```bash
curl "http://localhost:8000/api/v1/parse/results/550e8400-e29b-41d4-a716-446655440000"
```

**Response Structure:**
```json
{
  "job_id": "550e8400...",
  "status": "completed",
  "metadata": {
    "filename": "document.pdf",
    "page_count": 5,
    "file_size_bytes": 524288,
    "processing_time_ms": 2340
  },
  "statistics": {
    "total_text_items": 42,
    "total_tables": 3,
    "total_pictures": 8
  },
  "content": {
    "markdown": "# Document Title\n\nContent...",
    "texts": [...],
    "tables": [...],
    "pictures": [...]
  }
}
```

### 4. Get Only Tables as CSV

```bash
curl "http://localhost:8000/api/v1/parse/results/550e8400.../tables?format=csv"
```

### 5. Filter Text Items by Label

```bash
# Get only titles
curl "http://localhost:8000/api/v1/parse/results/550e8400.../texts?label=title"

# Get text from page 2
curl "http://localhost:8000/api/v1/parse/results/550e8400.../texts?page=2"
```

### 6. Export as Markdown

```bash
curl "http://localhost:8000/api/v1/parse/results/550e8400.../export/markdown" \
  -o output.md
```

---

## Parsing Modes

### Standard Mode (Default)
```bash
-F "parsing_mode=standard"
```
- Best for digital-born PDFs
- Fast processing
- Good text extraction

### OCR Mode
```bash
-F "parsing_mode=ocr"
```
- For scanned documents or images
- Slower processing
- Handles image-based text

### Fast Mode
```bash
-F "parsing_mode=fast"
```
- Quick extraction
- Lower accuracy
- Good for previews

### High Quality Mode
```bash
-F "parsing_mode=high_quality"
```
- Maximum accuracy
- Slower processing
- Advanced layout analysis

---

## Additional Options

### Image Extraction

```bash
curl -X POST "http://localhost:8000/api/v1/parse/document" \
  -F "file=@document.pdf" \
  -F "extract_images=true" \
  -F "images_scale=3.0"
```

### Disable Table Extraction

```bash
-F "extract_tables=false"
```

---

## Response Models

### Text Item
```json
{
  "label": "title",
  "text": "Document Title",
  "page": 1,
  "bbox": {
    "left": 72.0,
    "top": 100.0,
    "right": 540.0,
    "bottom": 120.0
  }
}
```

### Table Item
```json
{
  "id": "table-1",
  "page": 2,
  "rows": 5,
  "columns": 3,
  "data": {...},
  "dataframe_csv": "Name,Age,City\nJohn,30,NYC\n..."
}
```

### Picture Item
```json
{
  "id": "picture-1",
  "page": 3,
  "bbox": {...},
  "caption": "Figure 1: Classification diagram",
  "image_uri": "data:image/png;base64,iVBOR..."
}
```

---

## Python Client Example

```python
import requests
import time

# Upload document
response = requests.post(
    "http://localhost:8000/api/v1/parse/document",
    files={"file": open("document.pdf", "rb")},
    data={
        "parsing_mode": "standard",
        "extract_images": True
    }
)

job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/parse/jobs/{job_id}"
    )
    status = status_response.json()["status"]
    print(f"Status: {status}")

    if status == "completed":
        break
    elif status == "failed":
        print("Parsing failed!")
        exit(1)

    time.sleep(2)

# Get results
results = requests.get(
    f"http://localhost:8000/api/v1/parse/results/{job_id}"
).json()

print(f"Extracted {results['statistics']['total_text_items']} text items")
print(f"Found {results['statistics']['total_tables']} tables")
print(f"Found {results['statistics']['total_pictures']} images")

# Save markdown
with open("output.md", "w", encoding="utf-8") as f:
    f.write(results["content"]["markdown"])
```

---

## JavaScript Client Example

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('parsing_mode', 'standard');

const uploadResponse = await fetch('http://localhost:8000/api/v1/parse/document', {
  method: 'POST',
  body: formData
});

const { job_id } = await uploadResponse.json();

// Poll for completion
let status = 'pending';
while (status !== 'completed') {
  const statusResponse = await fetch(
    `http://localhost:8000/api/v1/parse/jobs/${job_id}`
  );
  const statusData = await statusResponse.json();
  status = statusData.status;

  if (status === 'failed') {
    throw new Error('Parsing failed');
  }

  await new Promise(resolve => setTimeout(resolve, 2000));
}

// Get results
const resultsResponse = await fetch(
  `http://localhost:8000/api/v1/parse/results/${job_id}`
);
const results = await resultsResponse.json();

console.log('Markdown:', results.content.markdown);
console.log('Tables:', results.content.tables);
```

---

## Configuration

Edit `config.py` to customize:

```python
# File Upload Settings
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".doc", ".html", ".md"]

# Storage Settings
RESULTS_TTL_SECONDS = 3600  # 1 hour

# Job Settings
JOB_TIMEOUT_SECONDS = 300  # 5 minutes
MAX_CONCURRENT_JOBS = 5

# Server Settings
HOST = "0.0.0.0"
PORT = 8000
```

---

## Error Handling

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNSUPPORTED_FILE_TYPE` | 400 | File type not supported |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `JOB_NOT_FOUND` | 404 | Invalid job ID |
| `PROCESSING` | 202 | Job still processing |
| `PARSING_FAILED` | 500 | Parsing error |
| `RESULT_EXPIRED` | 410 | Results no longer available |

### Error Response Format

```json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "File type 'application/zip' is not supported",
    "details": {
      "supported_types": ["application/pdf", "..."]
    }
  }
}
```

---

## Project Structure

```
api/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── models.py            # Pydantic models
├── parser.py            # Docling parsing logic
├── storage.py           # Job storage management
├── utils.py             # Helper functions
├── requirements.txt     # Dependencies
├── README.md           # This file
├── temp/               # Temporary uploaded files
└── output/             # Output directory
```

---

## Production Deployment

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t docling-api .
docker run -p 8000:8000 docling-api
```

### Production Considerations

1. **Replace In-Memory Storage**: Use Redis or PostgreSQL
2. **Use Message Queue**: Celery + Redis for job processing
3. **Add Authentication**: API keys or JWT tokens
4. **Enable Rate Limiting**: Prevent abuse
5. **Use HTTPS**: SSL/TLS certificates
6. **Add Monitoring**: Prometheus + Grafana
7. **Configure CORS**: Restrict allowed origins

---

## Supported File Types

- **PDF** (`.pdf`) - `application/pdf`
- **Word** (`.docx`) - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Word Legacy** (`.doc`) - `application/msword`
- **HTML** (`.html`, `.htm`) - `text/html`
- **Markdown** (`.md`) - `text/markdown`
- **Images** (`.png`, `.jpg`, `.tiff`) - with OCR mode

---

## Troubleshooting

### API won't start
- Check if port 8000 is available
- Verify dependencies are installed
- Check Python version (3.10+ required)

### Parsing takes too long
- Use `fast` parsing mode for quick preview
- Reduce `images_scale` parameter
- Disable image extraction if not needed

### Out of memory errors
- Reduce `MAX_CONCURRENT_JOBS` in config
- Process smaller files
- Increase system memory

### Results expired
- Increase `RESULTS_TTL_SECONDS` in config
- Retrieve results sooner after completion

---

## License

MIT License - See main project LICENSE file

---

## Support

For issues or questions:
- Check the interactive docs: http://localhost:8000/docs
- Review Docling documentation: https://github.com/DS4SD/docling
- Open an issue in the project repository

---

**Ready to parse documents!** 🚀
