# Text Items - Understanding Docling's Structured Text Extraction

## Overview

**Text items** are structured pieces of text extracted from your document by the Docling parser. Unlike simple text extraction that gives you raw strings, Docling provides **semantic understanding** of each text element, including its type, position, and context within the document.

## TextItem Data Structure

From `api/models.py`, here's the complete structure:

```python
class TextItem(BaseModel):
    label: str                    # Text type/category
    text: str                     # The actual text content
    page: Optional[int]           # Page number (0-indexed or 1-indexed)
    bbox: Optional[BoundingBox]   # Position coordinates on page
```

### BoundingBox Structure

```python
class BoundingBox(BaseModel):
    left: float      # Left edge X coordinate
    top: float       # Top edge Y coordinate
    right: float     # Right edge X coordinate
    bottom: float    # Bottom edge Y coordinate
```

## Fields Explained

### 1. `label` (string, required)

The semantic label that identifies what type of text this is. This is the **most important field** as it tells you the purpose and structure of the text.

**Common Label Types:**

| Label | Description | Example |
|-------|-------------|---------|
| `title` | Main document title or major headings | "Annual Report 2024" |
| `section_header` | Section headings and subheadings | "Introduction", "Methodology" |
| `paragraph` | Body text paragraphs | Regular content text |
| `list_item` | Bulleted or numbered list items | "• First item", "1. Step one" |
| `caption` | Figure or table captions | "Figure 1: Sales Growth" |
| `footnote` | Footnotes and references | "¹ Source: CDC 2023" |
| `page_header` | Header text on pages | "Chapter 3 - Results" |
| `page_footer` | Footer text on pages | "Page 15" |
| `formula` | Mathematical formulas | "E = mc²" |
| `code` | Code blocks or snippets | "def hello_world():" |
| `table` | Table text references | Reference to table content |
| `reference` | Bibliography references | Citation entries |

### 2. `text` (string, required)

The actual text content extracted from the document. This is the raw text string with whitespace normalized.

**Example:**
```json
{
  "text": "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems."
}
```

### 3. `page` (integer, optional)

The page number where this text item appears. May be `null` for certain document types that don't have page concepts (like HTML or Markdown).

**Example:**
```json
{
  "page": 1  // First page
}
```

### 4. `bbox` (BoundingBox, optional)

The bounding box coordinates that define the position of the text on the page. Coordinates are typically in points (1/72 of an inch) from the top-left corner of the page.

**Example:**
```json
{
  "bbox": {
    "left": 72.0,
    "top": 144.0,
    "right": 540.0,
    "bottom": 168.0
  }
}
```

This means the text starts 72 points from the left edge, 144 points from the top, and extends to 540 points horizontally and 168 points vertically.

## Complete Example

### Input Document
```
Annual Report 2024

Executive Summary
This year has been transformative for our company. We achieved:
• 25% revenue growth
• Expanded to 5 new markets
• Launched 3 innovative products

Financial Highlights
Revenue increased significantly...
```

### Extracted Text Items (JSON)

```json
[
  {
    "label": "title",
    "text": "Annual Report 2024",
    "page": 1,
    "bbox": {
      "left": 72.0,
      "top": 72.0,
      "right": 540.0,
      "bottom": 96.0
    }
  },
  {
    "label": "section_header",
    "text": "Executive Summary",
    "page": 1,
    "bbox": {
      "left": 72.0,
      "top": 120.0,
      "right": 400.0,
      "bottom": 136.0
    }
  },
  {
    "label": "paragraph",
    "text": "This year has been transformative for our company. We achieved:",
    "page": 1,
    "bbox": {
      "left": 72.0,
      "top": 150.0,
      "right": 540.0,
      "bottom": 166.0
    }
  },
  {
    "label": "list_item",
    "text": "25% revenue growth",
    "page": 1,
    "bbox": {
      "left": 90.0,
      "top": 170.0,
      "right": 540.0,
      "bottom": 186.0
    }
  },
  {
    "label": "list_item",
    "text": "Expanded to 5 new markets",
    "page": 1,
    "bbox": {
      "left": 90.0,
      "top": 190.0,
      "right": 540.0,
      "bottom": 206.0
    }
  },
  {
    "label": "list_item",
    "text": "Launched 3 innovative products",
    "page": 1,
    "bbox": {
      "left": 90.0,
      "top": 210.0,
      "right": 540.0,
      "bottom": 226.0
    }
  },
  {
    "label": "section_header",
    "text": "Financial Highlights",
    "page": 1,
    "bbox": {
      "left": 72.0,
      "top": 240.0,
      "right": 400.0,
      "bottom": 256.0
    }
  },
  {
    "label": "paragraph",
    "text": "Revenue increased significantly...",
    "page": 1,
    "bbox": {
      "left": 72.0,
      "top": 270.0,
      "right": 540.0,
      "bottom": 286.0
    }
  }
]
```

## Use Cases

### 1. **Document Structure Analysis**

Filter by label to understand document structure:

```python
# Get all section headers
headers = [item for item in text_items if item["label"] == "section_header"]

# Get document outline
titles = [item for item in text_items if item["label"] in ["title", "section_header"]]
```

### 2. **Content Extraction**

Extract specific content types:

```python
# Get all body text (no headers/footers)
body_text = [item["text"] for item in text_items if item["label"] == "paragraph"]

# Get all list items
bullet_points = [item["text"] for item in text_items if item["label"] == "list_item"]
```

### 3. **Page-Specific Content**

Filter content by page:

```python
# Get all content from page 5
page_5_content = [item for item in text_items if item["page"] == 5]

# Get page 1 title
page_1_title = next(
    (item for item in text_items if item["page"] == 1 and item["label"] == "title"),
    None
)
```

### 4. **Position-Based Processing**

Use bounding boxes for layout analysis:

```python
# Find text in top half of page
top_items = [
    item for item in text_items
    if item["bbox"] and item["bbox"]["top"] < 400
]

# Find text in left column (assuming two-column layout)
left_column = [
    item for item in text_items
    if item["bbox"] and item["bbox"]["left"] < 300
]
```

### 5. **Document Reconstruction**

Rebuild document with proper formatting:

```python
def reconstruct_document(text_items):
    output = []
    for item in text_items:
        if item["label"] == "title":
            output.append(f"# {item['text']}\n")
        elif item["label"] == "section_header":
            output.append(f"## {item['text']}\n")
        elif item["label"] == "paragraph":
            output.append(f"{item['text']}\n\n")
        elif item["label"] == "list_item":
            output.append(f"- {item['text']}\n")
    return "".join(output)
```

## API Endpoints for Text Items

### Get All Text Items

```http
GET /api/v1/parse/results/{job_id}
```

Returns complete results including all text items in `content.texts`.

### Get Filtered Text Items

```http
GET /api/v1/parse/results/{job_id}/texts?page=1&label=paragraph
```

**Query Parameters:**
- `page` (optional): Filter by specific page number
- `label` (optional): Filter by label type

**Example Response:**
```json
{
  "texts": [
    {
      "label": "paragraph",
      "text": "This is a paragraph on page 1...",
      "page": 1,
      "bbox": {...}
    }
  ],
  "count": 1,
  "page_filter": 1,
  "label_filter": "paragraph"
}
```

## UI Features

In the **Docling UI** (results.html), text items are displayed with:

1. **Visual Labels**: Each text item shows its label type in a colored badge
2. **Page Filtering**: Dropdown to filter by specific pages
3. **Label Filtering**: Dropdown to filter by label type
4. **Position Info**: Shows page number and bounding box coordinates
5. **Structured View**: Items are displayed in extraction order with clear separation

### Using Text Filters in UI

1. Navigate to the **Text Items** tab
2. Use **Filter by Page** dropdown to show content from specific pages
3. Use **Filter by Label** dropdown to show specific text types (e.g., only titles)
4. Click **Apply Filters** to update the view

## Benefits of Structured Text Items

### Compared to Plain Text Extraction

| Feature | Plain Text | Text Items |
|---------|-----------|------------|
| Content | ✓ Yes | ✓ Yes |
| Structure | ✗ No | ✓ Yes |
| Semantic Meaning | ✗ No | ✓ Yes |
| Position Data | ✗ No | ✓ Yes |
| Filtering | ✗ Limited | ✓ Advanced |
| Reconstruction | ✗ Difficult | ✓ Easy |

### Key Advantages

1. **Semantic Understanding**: Know what each text represents (title, paragraph, etc.)
2. **Accurate Filtering**: Get exactly the content you need
3. **Layout Preservation**: Maintain document structure
4. **Position Tracking**: Know where text appears on the page
5. **Easy Processing**: Process different text types differently
6. **Quality Output**: Generate better formatted exports

## Related Data Structures

Text items are part of a larger document structure:

### Document Content Structure

```python
class DocumentContent(BaseModel):
    markdown: str                    # Full document as markdown
    pages: List[PageInfo]            # Page metadata
    texts: List[TextItem]            # All text items
    tables: List[TableItem]          # Extracted tables
    pictures: List[PictureItem]      # Extracted images
```

### Complete Parse Result

```python
class ParseResultResponse(BaseModel):
    job_id: str                      # Job identifier
    status: JobStatus                # Processing status
    metadata: DocumentMetadata       # File info, processing time
    statistics: DocumentStatistics   # Counts of items
    content: DocumentContent         # Actual extracted content
    exports: ExportUrls              # URLs for exports
```

## Best Practices

### 1. Always Check for None Values

```python
# Safe access to optional fields
if item.get("page") is not None:
    print(f"Found on page {item['page']}")

if item.get("bbox"):
    print(f"Position: {item['bbox']['left']}, {item['bbox']['top']}")
```

### 2. Use Label Constants

```python
# Define constants for common labels
LABEL_TITLE = "title"
LABEL_HEADER = "section_header"
LABEL_PARAGRAPH = "paragraph"

# Use in filtering
headers = [item for item in texts if item["label"] in [LABEL_TITLE, LABEL_HEADER]]
```

### 3. Handle Different Document Types

```python
# Some documents may not have pages or bounding boxes
def safe_get_page(item):
    return item.get("page", "N/A")

def safe_get_position(item):
    if bbox := item.get("bbox"):
        return f"({bbox['left']:.0f}, {bbox['top']:.0f})"
    return "Unknown"
```

### 4. Combine with Other Content Types

```python
# Build complete document understanding
def analyze_document(result):
    text_count = len(result["content"]["texts"])
    table_count = len(result["content"]["tables"])
    image_count = len(result["content"]["pictures"])

    # Get structure
    titles = [t for t in result["content"]["texts"] if t["label"] == "title"]

    return {
        "text_items": text_count,
        "tables": table_count,
        "images": image_count,
        "document_title": titles[0]["text"] if titles else "Untitled"
    }
```

## Summary

Text items are the building blocks of Docling's intelligent document parsing. They provide:

- ✅ **Semantic labeling** of text elements
- ✅ **Positional data** for layout understanding
- ✅ **Structured filtering** capabilities
- ✅ **Document reconstruction** support
- ✅ **High-quality exports** with preserved formatting

By understanding and utilizing text items effectively, you can extract maximum value from your parsed documents and build sophisticated document processing workflows.

## See Also

- [API Models Reference](../api/models.py) - Complete Pydantic model definitions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [UI Guide](../UI/README.md) - Using the web interface
