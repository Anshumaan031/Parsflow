# Image Handling Guide for Docling

Complete guide to extracting, saving, and describing images from PDFs using Docling.

## Overview

Docling provides powerful image handling capabilities:
- **Extract images** from PDFs with high quality
- **Save images** to disk in various formats
- **AI-powered descriptions** using Vision-Language Models (VLMs)
- **Flexible export** to Markdown with different image modes
- **Metadata extraction** including captions, bounding boxes, page numbers

## Quick Start

### Basic Image Extraction

```bash
# Run the image handler
python image_handler.py
```

This will:
1. Extract all images from your PDF
2. Save images to `output/images/`
3. Create 4 different Markdown versions
4. Generate image metadata JSON

### AI-Powered Image Descriptions

```bash
# Run with AI descriptions (requires model download)
python image_description_vlm.py
```

This will:
1. Extract images
2. Generate AI descriptions for each image
3. Export Markdown with descriptions
4. Create custom formatted output

## Image Extraction Options

### 1. Basic Configuration

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.generate_picture_images = True  # Enable image extraction
pipeline_options.images_scale = 2.0              # Image quality (1.0-3.0)
```

**Image Scale Options:**
- `1.0` - Original size
- `2.0` - 2x size (recommended for quality)
- `3.0` - 3x size (high quality, larger files)

### 2. AI Image Descriptions

```python
pipeline_options.do_picture_description = True

# Option A: SmolVLM (Lightweight, ~500MB)
from docling.datamodel.pipeline_options import smolvlm_picture_description
pipeline_options.picture_description_options = smolvlm_picture_description

# Option B: Granite Vision (Powerful, ~2GB)
from docling.datamodel.pipeline_options import granite_picture_description
pipeline_options.picture_description_options = granite_picture_description

# Option C: Custom Hugging Face Model
from docling.datamodel.pipeline_options import PictureDescriptionVlmOptions
pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
    repo_id="your-model/repo-id",
    prompt="Describe this image in detail.",
)
```

### 3. Custom Prompts

```python
pipeline_options.picture_description_options.prompt = (
    "Describe this image in 2-3 sentences. "
    "Include any text, charts, diagrams, or key visual elements."
)
```

## Image Object Structure

Each `PictureItem` contains:

```python
picture = doc.pictures[0]

# Reference ID
picture.self_ref          # e.g., "#/pictures/0"

# Location
picture.prov[0].page_no   # Page number
picture.prov[0].bbox      # Bounding box (left, top, right, bottom)

# Image data
picture.image.uri         # Base64 data URI or file path
picture.image.size        # Image dimensions (if available)

# Caption
picture.caption_text(doc=doc)  # Original PDF caption

# AI annotations (if enabled)
picture.annotations       # List of PictureDescriptionData, etc.
```

## Markdown Export Modes

### Mode 1: Placeholder

Replace images with text placeholders.

```python
from docling_core.types.doc import ImageRefMode
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams

serializer = MarkdownDocSerializer(
    doc=doc,
    params=MarkdownParams(
        image_mode=ImageRefMode.PLACEHOLDER,
        image_placeholder="[IMAGE]",
    )
)
markdown = serializer.serialize().text
```

**Output:**
```markdown
Here is some text.

[IMAGE]

More text here.
```

**Best for:** Text-only exports, readability, small file sizes

### Mode 2: Embedded

Embed images as base64 data URIs.

```python
params=MarkdownParams(
    image_mode=ImageRefMode.EMBEDDED,
)
```

**Output:**
```markdown
![image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...)
```

**Best for:** Portable single-file documents, no external dependencies

**Caution:** Creates very large Markdown files

### Mode 3: Referenced

Reference images as external file paths.

```python
params=MarkdownParams(
    image_mode=ImageRefMode.REFERENCED,
)
```

**Output:**
```markdown
![image](./images/image_1.png)
```

**Best for:** Clean Markdown, separate image files, version control

**Note:** Requires images to be saved separately

### Mode 4: Custom Placeholder

Use custom text for each image.

```python
params=MarkdownParams(
    image_mode=ImageRefMode.PLACEHOLDER,
    image_placeholder="<!-- Image: See images folder -->",
)
```

**Output:**
```markdown
<!-- Image: See images folder -->
```

**Best for:** Custom workflows, image processing pipelines

## Saving Images

### Extract Base64 Images

```python
import base64
import re

for i, picture in enumerate(doc.pictures, 1):
    if picture.image and str(picture.image.uri).startswith('data:'):
        uri_str = str(picture.image.uri)

        # Parse data URI
        match = re.match(r'data:image/(\w+);base64,(.+)', uri_str)
        if match:
            image_format = match.group(1)  # png, jpeg, etc.
            image_data = base64.b64decode(match.group(2))

            # Save to file
            with open(f"image_{i}.{image_format}", 'wb') as f:
                f.write(image_data)
```

## AI Models Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **SmolVLM-256M** | ~500MB | Fast | Good | General descriptions, quick processing |
| **Granite Vision 3.1-2B** | ~2GB | Medium | Excellent | Detailed analysis, technical documents |
| **Custom HF Model** | Varies | Varies | Varies | Specialized tasks |

## Example Workflows

### Workflow 1: Extract All Images

```python
# 1. Configure
pipeline_options = PdfPipelineOptions()
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2.0

# 2. Convert
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
doc = converter.convert("document.pdf").document

# 3. Save all images
for i, picture in enumerate(doc.pictures):
    # Save image logic here
    pass
```

### Workflow 2: Generate Image Report

```python
# 1. Enable AI descriptions
pipeline_options.do_picture_description = True
from docling.datamodel.pipeline_options import smolvlm_picture_description
pipeline_options.picture_description_options = smolvlm_picture_description

# 2. Convert
doc = converter.convert("document.pdf").document

# 3. Create report
for i, picture in enumerate(doc.pictures):
    print(f"Image {i}:")
    print(f"  Page: {picture.prov[0].page_no}")
    print(f"  Caption: {picture.caption_text(doc=doc)}")

    for annotation in picture.annotations:
        if isinstance(annotation, PictureDescriptionData):
            print(f"  AI: {annotation.text}")
```

### Workflow 3: Markdown with Descriptions

```python
# Custom serializer with descriptions
from docling_core.transforms.serializer.markdown import MarkdownPictureSerializer

class DescriptivePictureSerializer(MarkdownPictureSerializer):
    def serialize(self, *, item, doc_serializer, doc, **kwargs):
        parts = [super().serialize(item=item, doc_serializer=doc_serializer, doc=doc, **kwargs).text]

        # Add descriptions
        for annotation in item.annotations:
            if isinstance(annotation, PictureDescriptionData):
                parts.append(f"\n*Description: {annotation.text}*\n")

        return create_ser_result(text="\n".join(parts), span_source=item)
```

## Performance Considerations

### Image Extraction
- **images_scale=1.0**: Fastest, smallest files
- **images_scale=2.0**: Recommended balance
- **images_scale=3.0**: High quality, slower, larger files

### AI Descriptions
- **First run**: Downloads model (5-15 minutes)
- **Subsequent runs**: Uses cached model (fast)
- **GPU**: Significantly faster if available
- **CPU**: Slower but works fine for small documents

### File Sizes
- **Placeholder mode**: Smallest Markdown files
- **Referenced mode**: Small MD, separate image files
- **Embedded mode**: Very large Markdown files (10x-100x)

## Troubleshooting

### Issue: "No images found"
- Check if PDF actually contains images
- Enable `generate_picture_images = True`
- Some PDFs have images as backgrounds (not extractable)

### Issue: "Model download fails"
- Check internet connection
- Ensure sufficient disk space (~2-5GB)
- Try manually: `huggingface-cli download model-name`

### Issue: "Out of memory"
- Reduce `images_scale` to 1.0
- Process fewer pages at once
- Close other applications
- Use CPU instead of GPU for small docs

### Issue: "Images not saving"
- Ensure output directory exists and is writable
- Check if images are data URIs (not external URLs)
- Verify image format is supported (png, jpeg, gif)

## Advanced Features

### Image Classification

```python
pipeline_options.do_picture_classification = True
```

Classifies images into categories:
- Charts (bar, line, pie, etc.)
- Diagrams
- Photos
- Screenshots
- etc.

### Custom Image Processing

```python
for picture in doc.pictures:
    # Access raw image data
    image_data = extract_image_data(picture)

    # Process with PIL, OpenCV, etc.
    from PIL import Image
    img = Image.open(BytesIO(image_data))
    img = img.resize((800, 600))
    img.save(f"processed_{picture.self_ref}.png")
```

## Files in This Project

| File | Purpose |
|------|---------|
| `image_handler.py` | Basic image extraction and export modes |
| `image_description_vlm.py` | AI-powered image descriptions |
| `IMAGE_HANDLING_GUIDE.md` | This guide |

## Next Steps

1. **Start simple:** Run `image_handler.py` to see basic extraction
2. **Try AI:** Run `image_description_vlm.py` for descriptions
3. **Customize:** Modify scripts for your specific needs
4. **Explore:** Check Docling docs for advanced features

## Resources

- **Docling Docs:** https://docling-project.github.io/docling/
- **Enrichments Guide:** https://docling-project.github.io/docling/usage/enrichments/
- **Examples:** https://github.com/docling-project/docling/tree/main/docs/examples
- **Hugging Face Models:** https://huggingface.co/models?pipeline_tag=image-to-text

## Model Download Sizes

When running AI descriptions for the first time:

```
SmolVLM (~500MB):
├── Model weights: ~470MB
├── Tokenizer: ~2MB
└── Config files: ~1MB

Granite Vision (~2GB):
├── Model weights: ~1.9GB
├── Tokenizer: ~5MB
└── Config files: ~2MB
```

Files are cached in: `~/.cache/huggingface/hub/`
