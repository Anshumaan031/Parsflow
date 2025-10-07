# Docling PDF Parser - Comprehensive Guide

## Overview

This guide explains the comprehensive PDF parser that shows you the complete internal structure of Docling's document extraction process.

## Installation

```bash
# Install docling
pip install docling

# Optional: Install pandas for better table display
pip install pandas
```

## Files

1. **`simple_pdf_parser.py`** - Minimal example for quick PDF to Markdown conversion
2. **`comprehensive_parser.py`** - Detailed inspection of document structure
3. **`basic_parsing.py`** - Your original script with stats

## What the Comprehensive Parser Shows

### 1. **ConversionResult Object**
- Conversion status (SUCCESS, FAILURE, PARTIAL_SUCCESS)
- Timing information
- Input source details
- Number of pages processed

### 2. **Document Object Structure**
The main `DoclingDocument` object contains:
- **`name`** - Document filename
- **`origin`** - Source metadata (filename, mimetype, binary hash)
- **`pages`** - List of page objects with dimensions
- **`texts`** - List of all text items with labels (heading, paragraph, list_item, etc.)
- **`tables`** - List of extracted tables
- **`pictures`** - List of images/figures
- **`key_value_items`** - Extracted key-value pairs
- **`body`** - Main content structure tree
- **`furniture`** - Headers, footers, page numbers

### 3. **Text Items**
Each `TextItem` includes:
- `text` - The actual text content
- `label` - Type (title, section_header, paragraph, list_item, caption, etc.)
- `prov` - Provenance (page number, bounding box coordinates)

### 4. **Table Items**
Each `TableItem` includes:
- `data` - Raw table data with cell information
- `export_to_dataframe()` - Convert to pandas DataFrame
- `export_to_dict()` - Convert to dictionary
- Cell coordinates and content

### 5. **Picture Items**
Each `PictureItem` includes:
- `image` - Image data with URI
- `prov` - Location on page
- `caption` - Associated caption text (if any)

### 6. **Document Hierarchy**
- `iterate_items()` - Walk through document in reading order with hierarchy levels
- `print_element_tree()` - Display hierarchical structure

### 7. **Export Formats**
- **Markdown** - `export_to_markdown()` - Human-readable format
- **Dictionary** - `export_to_dict()` - JSON-serializable structure
- **Document Tokens** - `export_to_document_tokens()` - Tokenized representation
- **Native JSON** - `save_as_json()` - Full Docling format with all metadata

## Running the Parser

```bash
# Run comprehensive parser
python comprehensive_parser.py

# Or run simple parser
python simple_pdf_parser.py
```

## Output Files

The parser creates an `output/` directory with:
- `document.md` - Markdown version
- `document.json` - Dictionary export
- `document_native.json` - Full Docling format

## Understanding the Output

### Document Flow:

```
ConversionResult
  ├── status (SUCCESS/FAILURE)
  ├── document (DoclingDocument)
  │     ├── origin (metadata)
  │     ├── pages[] (page objects)
  │     ├── texts[] (TextItem objects)
  │     │     ├── text (content)
  │     │     ├── label (type)
  │     │     └── prov (location)
  │     ├── tables[] (TableItem objects)
  │     │     ├── data (cells)
  │     │     └── export methods
  │     ├── pictures[] (PictureItem objects)
  │     └── body (NodeItem - content tree)
  │           └── children (hierarchy)
  └── pages[] (page-level metadata)
```

### Text Labels You'll See:
- `title` - Document title
- `section_header` - Section headings
- `paragraph` - Regular paragraphs
- `list_item` - Bullet/numbered lists
- `caption` - Figure/table captions
- `footnote` - Footnotes
- `page_header` / `page_footer` - Page furniture

### Table Structure:
Tables are extracted with full cell-level information including:
- Cell content
- Row/column spanning
- Header identification
- Cell coordinates

## Common Issues (Windows)

1. **Symlink Error:**
   ```python
   os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"  # Already included
   ```

2. **SSL Certificate Error:**
   ```bash
   pip install --upgrade certifi
   ```

3. **NumPy Version (Python 3.13):**
   ```bash
   pip install "numpy<2.0.0"
   ```

## Example Use Cases

### Extract all tables:
```python
for i, table in enumerate(doc.tables):
    df = table.export_to_dataframe()
    df.to_csv(f"table_{i}.csv")
```

### Get all headings:
```python
headings = [t.text for t in doc.texts if 'header' in t.label.lower()]
```

### Find specific content:
```python
for item, level in doc.iterate_items():
    if isinstance(item, TextItem) and 'keyword' in item.text.lower():
        print(f"Found at level {level}: {item.text}")
```

## Next Steps

1. Run `comprehensive_parser.py` to see the full structure
2. Examine the `output/document.json` to understand the data format
3. Review `output/document.md` to see the Markdown conversion
4. Modify the script to extract specific elements you need

## Documentation

- Official Docling Docs: https://docling-project.github.io/docling/
- GitHub: https://github.com/docling-project/docling
