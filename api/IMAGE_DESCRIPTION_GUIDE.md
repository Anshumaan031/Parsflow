# Image Description Guide

This guide explains how to use AI-powered image descriptions with the Docling Parser API.

## Overview

The API now supports automatic generation of detailed descriptions for images extracted from documents. This is especially useful for:
- **RAG (Retrieval-Augmented Generation)**: Enriching vector stores with image content
- **Accessibility**: Generating alt text for images
- **Document Understanding**: Getting detailed insights from charts, diagrams, and photos
- **Search & Indexing**: Making image content searchable

## Available Providers

### 1. **None** (Default)
- No image descriptions generated
- Fastest option
- Only extracts basic captions if available in document

### 2. **Docling** (Built-in SmolVLM)
- Uses Docling's built-in vision model (SmolVLM)
- Runs locally during parsing
- No API key required
- Free
- Good for basic descriptions
- Slightly slower parsing due to local model inference

### 3. **Gemini** (Google Gemini 2.0 Flash)
- Uses Google Gemini API via LangChain
- High-quality descriptions
- Fast and cost-effective
- Requires `GEMINI_API_KEY`
- Processes images after Docling extraction
- **Recommended for production**

### 4. **OpenAI** (GPT-4o Vision)
- Uses OpenAI GPT-4o via LangChain
- Highest quality descriptions
- More expensive than Gemini
- Requires `OPENAI_API_KEY`
- Best for detailed analysis

---

## Setup

### 1. Install Dependencies

For **Gemini**:
```bash
pip install langchain-google-genai
```

For **OpenAI**:
```bash
pip install langchain-openai
```

For **Docling VLM** (already installed):
```bash
# No additional dependencies needed
# SmolVLM is included with Docling
```

### 2. Configure API Keys

Create a `.env` file in the `api` directory:

```env
# For Gemini
GEMINI_API_KEY=your-gemini-api-key-here

# For OpenAI
OPENAI_API_KEY=your-openai-api-key-here
```

**Get API Keys:**
- Gemini: https://aistudio.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys

---

## Usage

### Via FastAPI Docs (Interactive)

1. Start the API:
   ```bash
   cd api
   python main.py
   ```

2. Open http://localhost:8000/docs

3. Use the `/api/v1/parse/document` endpoint with these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `describe_images` | boolean | `false` | Enable image descriptions |
| `description_provider` | enum | `none` | Provider: `none`, `docling`, `gemini`, `openai` |
| `description_prompt` | string | (optional) | Custom prompt for descriptions |

### Via Python Requests

#### Example 1: Using Gemini

```python
import requests

url = "http://localhost:8000/api/v1/parse/document"

with open("document.pdf", "rb") as f:
    files = {"file": f}
    params = {
        "parsing_mode": "high_quality",
        "extract_images": True,
        "images_scale": 2.0,
        "describe_images": True,
        "description_provider": "gemini"
    }

    response = requests.post(url, files=files, params=params)
    job_id = response.json()["job_id"]

print(f"Job ID: {job_id}")
```

#### Example 2: Using OpenAI with Custom Prompt

```python
params = {
    "describe_images": True,
    "description_provider": "openai",
    "description_prompt": "Analyze this chart/diagram. Describe the type of visualization, data shown, trends, and key insights in 2-3 sentences."
}
```

#### Example 3: Using Docling's Built-in VLM

```python
params = {
    "describe_images": True,
    "description_provider": "docling",
    "description_prompt": "Describe this image briefly."
}
```

### Via cURL

```bash
curl -X POST "http://localhost:8000/api/v1/parse/document" \
  -F "file=@document.pdf" \
  -F "parsing_mode=high_quality" \
  -F "extract_images=true" \
  -F "images_scale=2.5" \
  -F "describe_images=true" \
  -F "description_provider=gemini"
```

---

## Response Format

When image descriptions are enabled, each image in the response will include:

```json
{
  "pictures": [
    {
      "id": "picture-1",
      "page": 3,
      "bbox": {
        "left": 100.0,
        "top": 200.0,
        "right": 500.0,
        "bottom": 400.0
      },
      "caption": "Figure 3: Revenue Chart",
      "image_uri": "data:image/png;base64,...",
      "description": "This is a bar chart showing quarterly revenue from Q1 2023 to Q4 2023. The chart displays an upward trend with Q4 showing the highest revenue at approximately $2.5M. Colors used are blue for actual revenue and gray for projected revenue.",
      "description_provider": "gemini"
    }
  ]
}
```

**New Fields:**
- `description`: AI-generated detailed description
- `description_provider`: Provider used (`docling`, `gemini`, `openai`)

---

## Comparison of Providers

| Feature | None | Docling | Gemini | OpenAI |
|---------|------|---------|--------|--------|
| **Quality** | N/A | Good | Excellent | Excellent+ |
| **Speed** | Fastest | Slow | Fast | Medium |
| **Cost** | Free | Free | ~$0.001/image | ~$0.01/image |
| **API Key** | No | No | Yes | Yes |
| **Best For** | Simple extraction | Local/offline | Production RAG | High-accuracy needs |
| **Limitations** | No descriptions | Slower parsing | Requires internet | More expensive |

---

## Best Practices

### 1. Choose the Right Provider

- **For RAG Applications**: Use **Gemini** (fast, accurate, cost-effective)
- **For Offline/Local**: Use **Docling** (no API required)
- **For Critical Analysis**: Use **OpenAI** (highest quality)
- **For Speed**: Use **None** (no descriptions)

### 2. Custom Prompts

Tailor prompts to your use case:

**For Charts/Graphs:**
```
"Describe this chart/graph. Include: type of visualization, data shown, axes labels, trends, and key insights."
```

**For Diagrams:**
```
"Analyze this diagram. Describe the components, relationships, flow, and purpose."
```

**For Photos:**
```
"Describe this photo. Include: main subject, setting, important details, and any text visible."
```

**For Tables (as images):**
```
"Extract and describe the data in this table. Include column headers, row labels, and key values."
```

### 3. Performance Optimization

**Large Documents:**
```python
# Use high_quality mode with Gemini for best balance
params = {
    "parsing_mode": "high_quality",
    "images_scale": 2.0,
    "describe_images": True,
    "description_provider": "gemini"
}
```

**Many Images:**
- Consider processing in batches
- Use `fast` parsing mode if descriptions are the priority
- Gemini is faster than OpenAI for bulk processing

### 4. Error Handling

If description generation fails for an image:
- The API continues processing other images
- Failed images won't have `description` field
- Check logs for warnings

---

## Integration with RAG

### Example: Multimodal RAG Pipeline

```python
import requests
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# 1. Parse document with image descriptions
response = requests.post(
    "http://localhost:8000/api/v1/parse/document",
    files={"file": open("report.pdf", "rb")},
    params={
        "describe_images": True,
        "description_provider": "gemini",
        "images_scale": 2.5
    }
)
job_id = response.json()["job_id"]

# 2. Wait for completion and get results
# ... (polling logic) ...

result = requests.get(f"http://localhost:8000/api/v1/parse/results/{job_id}").json()

# 3. Create documents with image descriptions
documents = []

# Add text content
for text in result["content"]["texts"]:
    doc = Document(
        page_content=text["text"],
        metadata={"type": "text", "page": text["page"]}
    )
    documents.append(doc)

# Add image descriptions
for image in result["content"]["pictures"]:
    if image.get("description"):
        doc = Document(
            page_content=image["description"],
            metadata={
                "type": "image",
                "page": image["page"],
                "image_id": image["id"],
                "provider": image.get("description_provider")
            }
        )
        documents.append(doc)

# 4. Build vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# 5. Query
results = vectorstore.similarity_search("What does the revenue chart show?")
```

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not set"
**Solution:**
1. Get API key from https://aistudio.google.com/app/apikey
2. Create `.env` file in `api` directory
3. Add: `GEMINI_API_KEY=your-key-here`
4. Restart the API

### Issue: Descriptions are generic/poor quality
**Solution:**
1. Try a different provider (Gemini → OpenAI)
2. Use custom prompts with specific instructions
3. Increase `images_scale` for better image quality

### Issue: Slow parsing with Docling provider
**Solution:**
- Docling VLM runs locally and can be slow
- Consider using Gemini instead (faster, cloud-based)
- Or disable descriptions for faster parsing

### Issue: Images missing descriptions
**Possible Causes:**
- Image has no `image_uri` (extraction failed)
- API key is invalid or expired
- Network issues (for Gemini/OpenAI)
- Provider API rate limits

**Check logs for warnings:**
```
Warning: Failed to describe image picture-1: [error details]
```

---

## Cost Estimates

### Gemini (Recommended)
- Model: `gemini-2.0-flash-exp`
- Cost: ~$0.001 per image (approximate)
- 1000 images ≈ $1.00

### OpenAI
- Model: `gpt-4o`
- Cost: ~$0.01 per image (approximate)
- 1000 images ≈ $10.00

### Docling
- Free (local inference)
- Cost: Compute time only

---

## Examples

### Example 1: Research Paper with Charts

```python
params = {
    "parsing_mode": "high_quality",
    "extract_images": True,
    "images_scale": 3.0,
    "describe_images": True,
    "description_provider": "gemini",
    "description_prompt": "Analyze this figure from a research paper. Describe the type of visualization, data being presented, key findings, and any statistical significance indicators."
}
```

### Example 2: Business Report with Diagrams

```python
params = {
    "parsing_mode": "high_quality",
    "describe_images": True,
    "description_provider": "openai",
    "description_prompt": "Describe this business diagram. Include: type of diagram (flowchart, org chart, etc.), main components, relationships, and business insights."
}
```

### Example 3: Technical Manual with Screenshots

```python
params = {
    "parsing_mode": "standard",
    "describe_images": True,
    "description_provider": "gemini",
    "description_prompt": "Describe this UI screenshot. Include: application name, visible buttons/menus, user actions shown, and purpose of the screen."
}
```

---

## API Reference Summary

### New Parameters

**POST `/api/v1/parse/document`**

```
describe_images (boolean, default: false)
  Enable AI-generated image descriptions

description_provider (enum, default: "none")
  Options: "none", "docling", "gemini", "openai"

description_prompt (string, optional)
  Custom prompt for descriptions
  Default: "Describe this image in detail. Include what type of visual
           it is (chart, diagram, photo, etc.), main content, any text
           visible, and key insights."
```

### Response Changes

**PictureItem Object**

```json
{
  "id": "string",
  "page": "integer",
  "bbox": {...},
  "caption": "string",
  "image_uri": "string (base64 data URI)",
  "description": "string (NEW - AI-generated)",
  "description_provider": "string (NEW - provider used)"
}
```

---

## Next Steps

1. **Test the feature** with a sample document
2. **Experiment with prompts** to get optimal descriptions
3. **Integrate with RAG** if building a knowledge retrieval system
4. **Monitor costs** if using paid providers (Gemini/OpenAI)
5. **Provide feedback** on description quality

For more information, see:
- Main README: `../README.md`
- RAG Examples: `rag/README.md`
- API Documentation: http://localhost:8000/docs
