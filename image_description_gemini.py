"""
Image Description using Gemini API
Uses Google Gemini Vision API instead of local models
"""

import os
import base64
import re
from pathlib import Path

# Windows compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

def setup_gemini():
    """Setup Gemini API"""
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: google-generativeai not installed")
        print("Install with: pip install google-generativeai pillow")
        exit(1)

    # Get API key from environment (loaded from .env file)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found")
        print("\nTo set it up:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Create a .env file in the project folder with:")
        print("   GEMINI_API_KEY=your-api-key-here")
        print("\nOr set as environment variable:")
        print("   Windows: set GEMINI_API_KEY=your-api-key")
        print("   Linux/Mac: export GEMINI_API_KEY=your-api-key")
        exit(1)

    genai.configure(api_key=api_key)
    print(f"✓ API Key loaded (ends with: ...{api_key[-4:]})")
    return genai

def describe_image_with_gemini(genai, image_data, image_format, prompt):
    """Send image to Gemini and get description"""
    try:
        # Create model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Prepare image
        import PIL.Image
        from io import BytesIO

        image = PIL.Image.open(BytesIO(image_data))

        # Generate description
        response = model.generate_content([prompt, image])

        return response.text.strip()

    except Exception as e:
        return f"Error: {str(e)}"

def extract_image_data(picture):
    """Extract base64 image data from picture object"""
    if not (hasattr(picture, 'image') and picture.image):
        return None, None

    uri_str = str(picture.image.uri)

    if not uri_str.startswith('data:'):
        return None, None

    # Parse data URI
    match = re.match(r'data:image/(\w+);base64,(.+)', uri_str)
    if not match:
        return None, None

    image_format = match.group(1)
    image_base64 = match.group(2)
    image_data = base64.b64decode(image_base64)

    return image_data, image_format

def main():
    print("\n" + "="*80)
    print("  IMAGE DESCRIPTION WITH GEMINI API")
    print("="*80 + "\n")

    # Setup Gemini
    print("Setting up Gemini API...")
    genai = setup_gemini()
    print("✓ Gemini API configured\n")

    source = "picture_classification.pdf"
    print(f"Processing: {source}\n")

    # =========================================================================
    # EXTRACT IMAGES (without AI descriptions)
    # =========================================================================
    print("Extracting images from PDF...")

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2.0
    # Note: do_picture_description = False (we'll use Gemini instead)

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    result = converter.convert(source)
    doc = result.document

    print(f"✓ Extraction complete")
    print(f"✓ Status: {result.status}")
    print(f"✓ Images found: {len(doc.pictures)}\n")

    if not doc.pictures:
        print("No images found in document.")
        return

    # =========================================================================
    # DESCRIBE IMAGES WITH GEMINI
    # =========================================================================
    print("="*80)
    print("  GENERATING DESCRIPTIONS WITH GEMINI")
    print("="*80 + "\n")

    prompt = "Describe this image in a small paragraph. Be concise and accurate."

    image_descriptions = {}

    for i, picture in enumerate(doc.pictures, 1):
        print(f"Processing Image {i}/{len(doc.pictures)}...")

        # Extract image data
        image_data, image_format = extract_image_data(picture)

        if image_data is None:
            print(f"  ⚠ Could not extract image data\n")
            image_descriptions[picture.self_ref] = "Image data not available"
            continue

        # Get description from Gemini
        description = describe_image_with_gemini(genai, image_data, image_format, prompt)
        image_descriptions[picture.self_ref] = description

        print(f"  ✓ Description: {description[:80]}...")
        print()

    # =========================================================================
    # DISPLAY RESULTS
    # =========================================================================
    print("="*80)
    print("  RESULTS")
    print("="*80 + "\n")

    for i, picture in enumerate(doc.pictures, 1):
        print("-" * 80)
        print(f"IMAGE {i}")
        print("-" * 80)

        # Page info
        if picture.prov:
            print(f"Page: {picture.prov[0].page_no}")

        # Original caption
        caption = picture.caption_text(doc=doc) if hasattr(picture, 'caption_text') else None
        if caption:
            print(f"Original Caption: {caption}")

        # Gemini description
        description = image_descriptions.get(picture.self_ref, "No description")
        print(f"\nGemini Description:")
        print(f"  {description}")
        print()

    # =========================================================================
    # CREATE MARKDOWN WITH DESCRIPTIONS
    # =========================================================================
    print("="*80)
    print("  CREATING MARKDOWN OUTPUT")
    print("="*80 + "\n")

    from docling_core.types.doc import TextItem, PictureItem

    markdown_lines = ["# Document with Gemini Image Descriptions\n\n"]

    for item, level in doc.iterate_items():
        if isinstance(item, TextItem):
            # Add text content
            if item.label == "title":
                markdown_lines.append(f"# {item.text}\n\n")
            elif item.label == "section_header":
                markdown_lines.append(f"## {item.text}\n\n")
            elif item.label == "paragraph":
                markdown_lines.append(f"{item.text}\n\n")
            elif item.label == "list_item":
                markdown_lines.append(f"- {item.text}\n")

        elif isinstance(item, PictureItem):
            # Add image with Gemini description
            markdown_lines.append(f"\n---\n\n")
            markdown_lines.append(f"**📷 Image ({item.self_ref})**\n\n")

            # Page number
            if item.prov:
                markdown_lines.append(f"*Page {item.prov[0].page_no}*\n\n")

            # Original caption
            caption = item.caption_text(doc=doc) if hasattr(item, 'caption_text') else None
            if caption:
                markdown_lines.append(f"**Original Caption:** {caption}\n\n")

            # Gemini description
            description = image_descriptions.get(item.self_ref, "No description available")
            markdown_lines.append(f"**AI Description (Gemini):** {description}\n\n")

            markdown_lines.append(f"---\n\n")

    markdown_output = "".join(markdown_lines)

    # =========================================================================
    # SAVE OUTPUTS
    # =========================================================================
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save markdown with descriptions
    md_file = output_dir / "gemini_descriptions.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print(f"✓ Markdown with descriptions: {md_file}")

    # Save JSON with descriptions
    import json

    doc_dict = doc.export_to_dict()

    # Add Gemini descriptions to the JSON
    json_output = {
        "document": doc_dict,
        "gemini_descriptions": [
            {
                "image_ref": ref,
                "description": desc,
                "model": "gemini-2.5-flash"
            }
            for ref, desc in image_descriptions.items()
        ]
    }

    json_file = output_dir / "gemini_descriptions.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2)
    print(f"✓ JSON with descriptions: {json_file}")

    # Save images
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    for i, picture in enumerate(doc.pictures, 1):
        image_data, image_format = extract_image_data(picture)
        if image_data:
            image_file = images_dir / f"image_{i}.{image_format}"
            with open(image_file, "wb") as f:
                f.write(image_data)
            print(f"✓ Image {i}: {image_file}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80 + "\n")

    print(f"Total Images: {len(doc.pictures)}")
    print(f"Descriptions Generated: {len(image_descriptions)}")
    print(f"Model Used: Gemini 1.5 Flash")
    print(f"\nOutputs:")
    print(f"  • Markdown: {md_file}")
    print(f"  • JSON: {json_file}")
    print(f"  • Images: {images_dir}/")

    print("\n" + "="*80)
    print("\nPreview of output:\n")
    print(markdown_output[:600])
    print("...")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
