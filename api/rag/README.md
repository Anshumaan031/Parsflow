# RAG (Retrieval-Augmented Generation) Examples

This folder contains complete examples for using the Docling Parser API with RAG systems.

## Overview

These examples demonstrate how to:
1. Parse documents using the API
2. Extract and enrich images with vision models
3. Build multimodal vector stores
4. Query documents with text and image context

## Files

- **`simple_rag.py`** - Basic RAG pipeline with text-only
- **`multimodal_rag.py`** - Complete multimodal RAG with images
- **`image_enrichment.py`** - Image description generation for RAG
- **`requirements.txt`** - Python dependencies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
# Windows
set OPENAI_API_KEY=your-key-here

# Linux/Mac
export OPENAI_API_KEY=your-key-here
```

3. Make sure the Docling Parser API is running:
```bash
cd ..
python main.py
```

## Usage

### Simple Text-Only RAG
```bash
python simple_rag.py path/to/document.pdf "What is this document about?"
```

### Multimodal RAG with Images
```bash
python multimodal_rag.py path/to/document.pdf "Explain the chart in section 2"
```

### Generate Image Descriptions
```bash
python image_enrichment.py path/to/document.pdf
```

## Configuration

Edit the `API_BASE_URL` in each script if your API runs on a different host/port:
```python
API_BASE_URL = "http://localhost:8000"
```

## Features

### Simple RAG
- Text extraction and chunking
- Vector embeddings with OpenAI
- Basic similarity search
- Question answering

### Multimodal RAG
- Image extraction and description
- Combined text + image embeddings
- Vision model integration (GPT-4 Vision)
- Context-aware image retrieval
- Multimodal response generation

### Image Enrichment
- Automatic image description generation
- Caption enhancement
- Chart/diagram interpretation
- Table recognition in images

## Architecture

```
Document (PDF/DOCX)
    ↓
Docling Parser API
    ↓
Text + Images (Base64 URIs)
    ↓
Vision Model (GPT-4o)
    ↓
Enriched Descriptions
    ↓
Vector Embeddings (OpenAI)
    ↓
Vector Store (FAISS/Chroma)
    ↓
RAG Query System
```

## Example Output

```python
Query: "What does the revenue chart show?"

Retrieved Context:
1. [Text] "In Q4 2024, revenue increased by 25%..."
2. [Image] "Bar chart showing quarterly revenue from Q1-Q4 2024,
   with bars colored in blue, showing values: Q1: $2M, Q2: $2.5M,
   Q3: $3M, Q4: $3.75M. Y-axis shows revenue in millions,
   X-axis shows quarters."

Answer: "The revenue chart displays quarterly performance for 2024,
showing consistent growth from $2M in Q1 to $3.75M in Q4,
representing a 25% increase in the final quarter..."
```

## Notes

- **Image Scale**: Use higher values (3.0-4.0) for better OCR on charts
- **Processing Time**: Vision model calls add ~2-3 seconds per image
- **Cost**: GPT-4 Vision is more expensive than text-only models
- **Storage**: Base64 images increase vector store size significantly

## Best Practices

1. **Filter Images**: Only describe relevant images (skip decorative ones)
2. **Batch Processing**: Process multiple images in parallel
3. **Caching**: Cache image descriptions to avoid redundant API calls
4. **Metadata**: Store original image URIs for later reference
5. **Chunking**: Split long texts while preserving image context

## Troubleshooting

**Issue**: "Module 'langchain' not found"
- Solution: `pip install -r requirements.txt`

**Issue**: "Connection refused to localhost:8000"
- Solution: Start the API with `python main.py` from api folder

**Issue**: "OpenAI API key not found"
- Solution: Set environment variable `OPENAI_API_KEY`

**Issue**: "Out of memory" with large PDFs
- Solution: Use `parsing_mode=fast` or process pages in batches
