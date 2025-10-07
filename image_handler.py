"""
PDF Image Handler with Docling
Extract, save, and describe images from PDFs
"""

import os
import json
from pathlib import Path

# Disable symlinks for Windows compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def main():
    source = "picture_classification.pdf"

    print_section("IMAGE EXTRACTION AND HANDLING")
    print(f"Processing: {source}\n")

    # =========================================================================
    # CONFIGURATION: Enable image extraction
    # =========================================================================
    print("Configuring image extraction options:")
    print("  ✓ generate_picture_images = True (extract and save images)")
    print("  ✓ images_scale = 2.0 (higher quality)")

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True  # Extract images
    pipeline_options.images_scale = 2.0  # Image quality (1.0 = original, 2.0 = 2x)

    # Optional: Enable AI-powered image descriptions
    # Requires VLM models - uncomment to enable
    pipeline_options.do_picture_description = True
    from docling.datamodel.pipeline_options import smolvlm_picture_description
    pipeline_options.picture_description_options = smolvlm_picture_description
    pipeline_options.picture_description_options.prompt = "Describe this image in 2-3 sentences."

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

    print("\nConverting document...")
    result = converter.convert(source)
    doc = result.document
    print(f"✓ Conversion Status: {result.status}")

    # =========================================================================
    # ANALYZE IMAGES
    # =========================================================================
    print_section(f"IMAGES FOUND: {len(doc.pictures)}")

    if not doc.pictures:
        print("No images found in the document.")
        return

    # Create output directory for images
    output_dir = Path("output/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each image
    for i, picture in enumerate(doc.pictures, 1):
        print(f"\n--- Image {i} ---")
        print(f"Reference ID: {picture.self_ref}")

        # Page information
        if picture.prov:
            page_info = picture.prov[0]
            print(f"Page: {page_info.page_no}")
            print(f"Bounding Box: L={page_info.bbox.l:.1f}, T={page_info.bbox.t:.1f}, "
                  f"R={page_info.bbox.r:.1f}, B={page_info.bbox.b:.1f}")

        # Image URI and file info
        if hasattr(picture, 'image') and picture.image:
            print(f"Image URI: {picture.image.uri}")

            # Try to get image size
            if hasattr(picture.image, 'size'):
                print(f"Image Size: {picture.image.size}")

        # Caption
        caption = picture.caption_text(doc=doc) if hasattr(picture, 'caption_text') else None
        if caption:
            print(f"Caption: {caption[:100]}..." if len(caption) > 100 else f"Caption: {caption}")
        else:
            print("Caption: None")

        # Annotations (if picture description was enabled)
        if hasattr(picture, 'annotations') and picture.annotations:
            print("Annotations:")
            for annotation in picture.annotations:
                print(f"  - {type(annotation).__name__}: {str(annotation)[:100]}")

        # Save image if available
        if hasattr(picture, 'image') and picture.image and hasattr(picture.image, 'uri'):
            uri_str = str(picture.image.uri)

            # If it's a data URI or base64, try to save it
            if uri_str.startswith('data:'):
                try:
                    import base64
                    import re

                    # Extract base64 data
                    match = re.match(r'data:image/(\w+);base64,(.+)', uri_str)
                    if match:
                        image_format = match.group(1)
                        image_data = base64.b64decode(match.group(2))

                        # Save image
                        image_filename = output_dir / f"image_{i}.{image_format}"
                        with open(image_filename, 'wb') as f:
                            f.write(image_data)
                        print(f"✓ Saved to: {image_filename}")
                except Exception as e:
                    print(f"✗ Could not save image: {e}")

    # =========================================================================
    # EXPORT OPTIONS
    # =========================================================================
    print_section("MARKDOWN EXPORT OPTIONS")

    # Option 1: Images as placeholders
    print("Option 1: Image Placeholders")
    print("-" * 40)
    serializer = MarkdownDocSerializer(
        doc=doc,
        params=MarkdownParams(
            image_mode=ImageRefMode.PLACEHOLDER,
            image_placeholder="[IMAGE]",
        )
    )
    md_placeholder = serializer.serialize().text
    print(md_placeholder[:500])
    print("...\n")

    # Option 2: Images as embedded data URIs
    print("Option 2: Embedded Images (data URIs)")
    print("-" * 40)
    serializer = MarkdownDocSerializer(
        doc=doc,
        params=MarkdownParams(
            image_mode=ImageRefMode.EMBEDDED,
        )
    )
    md_embedded = serializer.serialize().text
    print(md_embedded[:500])
    print("...\n")

    # Option 3: Images as file references
    print("Option 3: Referenced Images (local files)")
    print("-" * 40)
    serializer = MarkdownDocSerializer(
        doc=doc,
        params=MarkdownParams(
            image_mode=ImageRefMode.REFERENCED,
        )
    )
    md_referenced = serializer.serialize().text
    print(md_referenced[:500])
    print("...\n")

    # Option 4: Custom placeholder with description
    print("Option 4: Custom Placeholder")
    print("-" * 40)
    serializer = MarkdownDocSerializer(
        doc=doc,
        params=MarkdownParams(
            image_mode=ImageRefMode.PLACEHOLDER,
            image_placeholder="<!-- Image: See images folder -->",
        )
    )
    md_custom = serializer.serialize().text
    print(md_custom[:500])
    print("...\n")

    # =========================================================================
    # SAVE ALL VERSIONS
    # =========================================================================
    print_section("SAVING OUTPUTS")

    output_files = {
        "markdown_placeholder.md": md_placeholder,
        "markdown_embedded.md": md_embedded,
        "markdown_referenced.md": md_referenced,
        "markdown_custom.md": md_custom,
    }

    for filename, content in output_files.items():
        filepath = Path("output") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Saved: {filepath}")

    # Save image metadata
    image_metadata = []
    for i, picture in enumerate(doc.pictures, 1):
        metadata = {
            "index": i,
            "ref_id": picture.self_ref,
            "page": picture.prov[0].page_no if picture.prov else None,
            "bbox": {
                "left": picture.prov[0].bbox.l if picture.prov else None,
                "top": picture.prov[0].bbox.t if picture.prov else None,
                "right": picture.prov[0].bbox.r if picture.prov else None,
                "bottom": picture.prov[0].bbox.b if picture.prov else None,
            } if picture.prov else None,
            "caption": picture.caption_text(doc=doc) if hasattr(picture, 'caption_text') else None,
            "has_image": bool(hasattr(picture, 'image') and picture.image),
        }
        image_metadata.append(metadata)

    metadata_file = Path("output/images/metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(image_metadata, f, indent=2)
    print(f"✓ Image metadata: {metadata_file}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("SUMMARY")
    print(f"Total Images Extracted: {len(doc.pictures)}")
    print(f"Images Saved to: {output_dir.absolute()}")
    print(f"Markdown Versions: {len(output_files)}")
    print("\nMarkdown Export Modes:")
    print("  1. Placeholder - Images replaced with text (best for text-only)")
    print("  2. Embedded - Images as base64 data URIs (portable but large)")
    print("  3. Referenced - Images as file paths (requires external files)")
    print("  4. Custom - Your own placeholder text")
    print("\nTo enable AI image descriptions, uncomment the VLM options in the code.")
    print("="*80)

if __name__ == "__main__":
    main()
