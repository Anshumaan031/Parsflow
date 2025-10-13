"""
AI-Powered Image Description with Docling
Uses Vision-Language Models to automatically describe images in PDFs
"""

import os
from pathlib import Path

# Disable symlinks for Windows compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionVlmOptions
from docling_core.types.doc.document import PictureDescriptionData
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    source = "picture_classification.pdf"

    print_section("AI IMAGE DESCRIPTION WITH VLM")
    print(f"Processing: {source}\n")

    print("NOTE: This script uses AI models to describe images.")
    print("First run will download VLM models (~500MB-2GB).")
    print("Requires internet connection and may take a few minutes.\n")

    # =========================================================================
    # OPTION 1: SmolVLM (Lightweight, Recommended)
    # =========================================================================
    print("Using: SmolVLM-256M-Instruct (Lightweight)")
    print("  - Model size: ~500MB")
    print("  - Speed: Fast")
    print("  - Quality: Good for general descriptions\n")

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2.0
    pipeline_options.do_picture_description = True

    # SmolVLM configuration
    from docling.datamodel.pipeline_options import smolvlm_picture_description
    pipeline_options.picture_description_options = smolvlm_picture_description
    pipeline_options.picture_description_options.prompt = (
        "Describe this image in a short paragraph. Be concise and accurate."
    )

    # =========================================================================
    # OPTION 2: Granite Vision (IBM, More Powerful)
    # Uncomment to use instead of SmolVLM
    # =========================================================================
    # print("Using: Granite Vision 3.1-2B (More Powerful)")
    # from docling.datamodel.pipeline_options import granite_picture_description
    # pipeline_options.picture_description_options = granite_picture_description
    # pipeline_options.picture_description_options.prompt = (
    #     "Describe this image in detail, including any text, charts, or diagrams."
    # )

    # =========================================================================
    # OPTION 3: Custom Hugging Face Model
    # Uncomment and add your model repo_id
    # =========================================================================
    # pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
    #     repo_id="your-model/repo-id",
    #     prompt="Your custom prompt here.",
    # )

    # =========================================================================
    # CONVERT DOCUMENT
    # =========================================================================
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    print("Converting and describing images...")
    print("(This may take a minute on first run)\n")

    result = converter.convert(source)
    doc = result.document
    print(f"✓ Conversion Status: {result.status}")

    # =========================================================================
    # DISPLAY IMAGE DESCRIPTIONS
    # =========================================================================
    print_section(f"IMAGE DESCRIPTIONS ({len(doc.pictures)} images)")

    if not doc.pictures:
        print("No images found in the document.")
        return

    for i, picture in enumerate(doc.pictures, 1):
        print(f"\n{'─'*80}")
        print(f"IMAGE {i}")
        print(f"{'─'*80}")

        # Basic info
        print(f"Reference: {picture.self_ref}")
        if picture.prov:
            print(f"Page: {picture.prov[0].page_no}")

        # Original caption from PDF
        caption = picture.caption_text(doc=doc) if hasattr(picture, 'caption_text') else None
        if caption:
            print(f"\nOriginal Caption:")
            print(f"  {caption}")

        # AI-generated description
        if hasattr(picture, 'annotations') and picture.annotations:
            print(f"\nAI Description:")
            for annotation in picture.annotations:
                if isinstance(annotation, PictureDescriptionData):
                    print(f"  Model: {annotation.provenance}")
                    print(f"  Description: {annotation.text}")
        else:
            print("\nAI Description: Not available")

    # =========================================================================
    # EXPORT WITH DESCRIPTIONS
    # =========================================================================
    print_section("MARKDOWN EXPORT WITH DESCRIPTIONS")

    # Default export includes descriptions as comments
    serializer = MarkdownDocSerializer(doc=doc)
    markdown_with_descriptions = serializer.serialize().text

    # Save output
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "document_with_image_descriptions.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_with_descriptions)

    print(f"✓ Saved: {output_file}")
    print("\nPreview (first 800 characters):")
    print("─" * 80)
    print(markdown_with_descriptions[:800])
    print("...")
    print("─" * 80)

    # =========================================================================
    # CREATE CUSTOM FORMAT WITH DESCRIPTIONS
    # =========================================================================
    print_section("CUSTOM FORMAT: Images with Descriptions")

    custom_output = []
    custom_output.append("# Document with AI-Described Images\n")

    # Export text and images with descriptions
    for item, level in doc.iterate_items():
        from docling_core.types.doc import TextItem, PictureItem

        if isinstance(item, TextItem):
            # Add text items
            if item.label == "title":
                custom_output.append(f"\n# {item.text}\n")
            elif item.label == "section_header":
                custom_output.append(f"\n{'#' * (level + 1)} {item.text}\n")
            elif item.label == "paragraph":
                custom_output.append(f"\n{item.text}\n")

        elif isinstance(item, PictureItem):
            # Add images with descriptions
            custom_output.append(f"\n---\n")
            custom_output.append(f"**Image {item.self_ref}**\n\n")

            # Caption
            caption = item.caption_text(doc=doc) if hasattr(item, 'caption_text') else None
            if caption:
                custom_output.append(f"*Caption:* {caption}\n\n")

            # AI Description
            if hasattr(item, 'annotations'):
                for annotation in item.annotations:
                    if isinstance(annotation, PictureDescriptionData):
                        custom_output.append(f"*AI Description:* {annotation.text}\n\n")

            custom_output.append(f"---\n")

    custom_markdown = "".join(custom_output)

    # Save custom format
    custom_file = output_dir / "custom_image_descriptions.md"
    with open(custom_file, "w", encoding="utf-8") as f:
        f.write(custom_markdown)

    print(f"✓ Saved: {custom_file}")
    print("\nPreview:")
    print("─" * 80)
    print(custom_markdown[:600])
    print("...")
    print("─" * 80)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("SUMMARY")
    print(f"Images Processed: {len(doc.pictures)}")
    print(f"Outputs:")
    print(f"  1. Standard markdown: {output_file}")
    print(f"  2. Custom format: {custom_file}")
    print("\nModel Used: SmolVLM-256M-Instruct")
    print("\nTo use different models:")
    print("  - Granite Vision: Uncomment Option 2 in the code")
    print("  - Custom model: Add your Hugging Face repo_id in Option 3")
    print("="*80)

if __name__ == "__main__":
    main()
