"""
Comprehensive PDF Parser with Docling
Shows the complete structure of extracted documents
"""

import os
import json
from pathlib import Path
from pprint import pprint

# Disable symlinks for Windows compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from docling.document_converter import DocumentConverter
from docling_core.types.doc import TextItem, TableItem, PictureItem

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    # Source PDF
    source = "picture_classification.pdf"

    print_section("1. CONVERSION PROCESS")
    print(f"Converting: {source}")

    # Initialize converter
    converter = DocumentConverter()

    # Convert the document
    result = converter.convert(source)

    print(f"✓ Conversion Status: {result.status}")
    print(f"✓ Conversion Time: {result.timings.get('total', 'N/A')} seconds" if hasattr(result, 'timings') else "")

    # =========================================================================
    print_section("2. CONVERSION RESULT OBJECT STRUCTURE")
    print("ConversionResult attributes:")
    print(f"  - status: {result.status}")
    print(f"  - document: DoclingDocument object")

    # Print available attributes
    result_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
    print(f"  - Available attributes: {', '.join(result_attrs[:10])}...")

    if hasattr(result, 'input'):
        print(f"  - input: {result.input}")
    if hasattr(result, 'pages'):
        print(f"  - pages: {len(result.pages)} pages")

    # =========================================================================
    print_section("3. DOCUMENT OBJECT - MAIN PROPERTIES")
    doc = result.document

    print(f"Document Name: {doc.name if hasattr(doc, 'name') else 'N/A'}")

    if hasattr(doc, 'origin'):
        print(f"Origin:")
        print(f"  - Filename: {doc.origin.filename if hasattr(doc.origin, 'filename') else 'N/A'}")
        print(f"  - Mimetype: {doc.origin.mimetype if hasattr(doc.origin, 'mimetype') else 'N/A'}")
        print(f"  - Binary Hash: {doc.origin.binary_hash if hasattr(doc.origin, 'binary_hash') else 'N/A'}")
    else:
        print("Origin: N/A")

    # =========================================================================
    print_section("4. DOCUMENT CONTENT STATISTICS")
    print(f"Total Pages: {len(doc.pages)}")
    print(f"Total Text Items: {len(doc.texts)}")
    print(f"Total Tables: {len(doc.tables)}")
    print(f"Total Pictures: {len(doc.pictures)}")
    print(f"Total Key-Value Items: {len(doc.key_value_items) if hasattr(doc, 'key_value_items') else 0}")

    # =========================================================================
    print_section("5. PAGE-BY-PAGE BREAKDOWN")
    for i, page in enumerate(doc.pages, 1):
        print(f"Page {i}:")
        # Check if page is an object or just a number
        if isinstance(page, int):
            print(f"  - Page Number: {page}")
        else:
            print(f"  - Page Number: {page.page_no if hasattr(page, 'page_no') else i}")
            if hasattr(page, 'size'):
                print(f"  - Size: {page.size.width} x {page.size.height}")
            if hasattr(page, 'image') and page.image:
                print(f"  - Image: {page.image.uri}")

    # =========================================================================
    print_section("6. TEXT ITEMS SAMPLE")
    print(f"Showing first 5 text items (out of {len(doc.texts)}):\n")
    for i, text_item in enumerate(doc.texts[:5], 1):
        print(f"Text Item {i}:")
        print(f"  - Label: {text_item.label}")
        print(f"  - Text: {text_item.text[:100]}..." if len(text_item.text) > 100 else f"  - Text: {text_item.text}")
        print(f"  - Page: {text_item.prov[0].page_no if text_item.prov else 'N/A'}")
        print()

    # =========================================================================
    print_section("7. TABLES DETAILED INSPECTION")
    if doc.tables:
        print(f"Found {len(doc.tables)} table(s)\n")
        for i, table in enumerate(doc.tables[:2], 1):  # Show first 2 tables
            print(f"Table {i}:")
            print(f"  - Self-ref: {table.self_ref}")

            # Export table to pandas DataFrame
            try:
                import pandas as pd
                df = table.export_to_dataframe()
                print(f"  - Shape: {df.shape[0]} rows x {df.shape[1]} columns")
                print(f"  - Preview:")
                print(df.head().to_string(index=False))
            except Exception as e:
                print(f"  - Could not export to DataFrame: {e}")

            # Table data in dict format
            print(f"\n  - Table Data (dict):")
            table_dict = table.export_to_dict()
            print(f"    {json.dumps(table_dict, indent=4)[:500]}...")
            print()
    else:
        print("No tables found in document")

    # =========================================================================
    print_section("8. PICTURES INSPECTION")
    if doc.pictures:
        print(f"Found {len(doc.pictures)} picture(s)\n")
        for i, picture in enumerate(doc.pictures[:3], 1):  # Show first 3 pictures
            print(f"Picture {i}:")
            print(f"  - Self-ref: {picture.self_ref}")
            print(f"  - Page: {picture.prov[0].page_no if picture.prov else 'N/A'}")
            if hasattr(picture, 'image') and picture.image:
                print(f"  - Image URI: {picture.image.uri}")
                print(f"  - Size: {picture.image.size if hasattr(picture.image, 'size') else 'N/A'}")
            if hasattr(picture, 'caption') and picture.caption:
                caption_text = picture.caption.text if hasattr(picture.caption, 'text') else str(picture.caption)
                print(f"  - Caption: {caption_text[:100]}...")
            print()
    else:
        print("No pictures found in document")

    # =========================================================================
    print_section("9. DOCUMENT ELEMENT TREE")
    print("Hierarchical structure of document elements:\n")
    try:
        doc.print_element_tree()
    except Exception as e:
        print(f"Could not print element tree: {e}")
        print("Trying alternative: listing main components...")
        print(f"  - Body: {doc.body if hasattr(doc, 'body') else 'N/A'}")
        print(f"  - Furniture: {doc.furniture if hasattr(doc, 'furniture') else 'N/A'}")

    # =========================================================================
    print_section("10. ITERATING THROUGH DOCUMENT ITEMS")
    print("Showing first 10 items with their hierarchy level:\n")
    try:
        for idx, (item, level) in enumerate(doc.iterate_items()):
            if idx >= 10:
                break
            indent = "  " * level
            if isinstance(item, TextItem):
                item_type = f"TextItem ({item.label})"
                content = item.text[:50] + "..." if len(item.text) > 50 else item.text
            elif isinstance(item, TableItem):
                item_type = "TableItem"
                content = f"Table with {len(item.data.table_cells) if hasattr(item.data, 'table_cells') else 'N/A'} cells"
            elif isinstance(item, PictureItem):
                item_type = "PictureItem"
                content = "Image"
            else:
                item_type = type(item).__name__
                content = ""

            print(f"{indent}[Level {level}] {item_type}: {content}")
    except Exception as e:
        print(f"Could not iterate items: {e}")

    # =========================================================================
    print_section("11. EXPORT TO DIFFERENT FORMATS")

    # Export to Markdown
    print("A. Markdown Export (first 500 characters):")
    markdown = doc.export_to_markdown()
    print("-" * 80)
    print(markdown[:500])
    print("...\n")
    print(f"Total Markdown Length: {len(markdown)} characters")

    # Export to Dictionary (JSON-serializable)
    print("\nB. Dictionary Export (structure only):")
    doc_dict = doc.export_to_dict()
    print(f"Top-level keys: {list(doc_dict.keys())}")
    print(f"Number of texts: {len(doc_dict.get('texts', []))}")
    print(f"Number of tables: {len(doc_dict.get('tables', []))}")
    print(f"Number of pictures: {len(doc_dict.get('pictures', []))}")

    # Export to Document Tokens
    print("\nC. Document Tokens Export (first 20 tokens):")
    try:
        tokens = doc.export_to_document_tokens()
        print(tokens[:20] if isinstance(tokens, list) else str(tokens)[:500])
    except Exception as e:
        print(f"Could not export to tokens: {e}")

    # =========================================================================
    print_section("12. SAVING OUTPUTS")

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save Markdown
    md_file = output_dir / "document.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"✓ Markdown saved to: {md_file}")

    # Save JSON
    json_file = output_dir / "document.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(doc_dict, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON saved to: {json_file}")

    # Save raw document using docling's native save
    try:
        native_json_file = output_dir / "document_native.json"
        doc.save_as_json(native_json_file)
        print(f"✓ Native Docling JSON saved to: {native_json_file}")
    except Exception as e:
        print(f"✗ Could not save native format: {e}")

    # =========================================================================
    print_section("13. SUMMARY")
    print(f"Document: {doc.name}")
    print(f"Pages: {len(doc.pages)}")
    print(f"Text Items: {len(doc.texts)}")
    print(f"Tables: {len(doc.tables)}")
    print(f"Pictures: {len(doc.pictures)}")
    print(f"\nAll outputs saved to: {output_dir.absolute()}")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
