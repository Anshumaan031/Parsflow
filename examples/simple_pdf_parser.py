"""
Simple PDF to Markdown Conversion with Docling
"""

from docling.document_converter import DocumentConverter

# Path to your PDF file or URL
source = "picture_classification.pdf"  # Can also be a URL like "https://arxiv.org/pdf/2408.09869"

# Initialize converter
converter = DocumentConverter()

# Convert the PDF
result = converter.convert(source)

# Export to Markdown
markdown_output = result.document.export_to_markdown()

# Save to file
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown_output)

# Print preview
print("Conversion completed!")
print(f"Status: {result.status}")
print("\nFirst 500 characters:")
print(markdown_output[:500])
