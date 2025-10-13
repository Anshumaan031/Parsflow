"""
Utility functions for file handling and data extraction
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import UploadFile, HTTPException

from config import settings
from models import (
    BoundingBox, TextItem, TableItem, PictureItem,
    PageInfo, DocumentMetadata, DocumentStatistics
)


# ============================================================================
# FILE HANDLING
# ============================================================================

def validate_file(file: UploadFile) -> str:
    """
    Validate uploaded file and return content type

    Args:
        file: Uploaded file

    Returns:
        Content type of the file

    Raises:
        HTTPException: If file is invalid
    """
    # Check if file exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNSUPPORTED_FILE_TYPE",
                "message": f"File extension '{file_ext}' is not supported",
                "supported_extensions": settings.ALLOWED_EXTENSIONS
            }
        )

    # Detect content type
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]

    if content_type not in settings.SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNSUPPORTED_MIME_TYPE",
                "message": f"MIME type '{content_type}' is not supported",
                "supported_types": list(settings.SUPPORTED_MIME_TYPES.keys())
            }
        )

    return content_type


async def save_upload_file(file: UploadFile, job_id: str) -> Path:
    """
    Save uploaded file to temporary directory

    Args:
        file: Uploaded file
        job_id: Job identifier

    Returns:
        Path to saved file
    """
    # Create job-specific temp directory
    job_dir = settings.TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    file_ext = Path(file.filename).suffix
    safe_filename = f"{job_id}{file_ext}"
    file_path = job_dir / safe_filename

    # Save file
    try:
        contents = await file.read()

        # Check file size
        if len(contents) > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
                    "max_size_mb": settings.MAX_FILE_SIZE_MB
                }
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        return file_path

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


def cleanup_job_files(job_id: str):
    """
    Clean up temporary files for a job

    Args:
        job_id: Job identifier
    """
    job_dir = settings.TEMP_DIR / job_id
    if job_dir.exists():
        import shutil
        try:
            shutil.rmtree(job_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup job files for {job_id}: {e}")


# ============================================================================
# DATA EXTRACTION FROM DOCLING DOCUMENT
# ============================================================================

def extract_metadata(doc: Any, result: Any, filename: str, file_size: Optional[int] = None) -> DocumentMetadata:
    """
    Extract document metadata

    Args:
        doc: Docling document object
        result: Conversion result object
        filename: Original filename
        file_size: File size in bytes

    Returns:
        DocumentMetadata object
    """
    # Get binary_hash and convert to string if needed
    binary_hash = None
    if hasattr(doc, 'origin') and hasattr(doc.origin, 'binary_hash'):
        binary_hash = str(doc.origin.binary_hash) if doc.origin.binary_hash is not None else None

    metadata = DocumentMetadata(
        filename=filename,
        mimetype=doc.origin.mimetype if hasattr(doc, 'origin') and hasattr(doc.origin, 'mimetype') else None,
        binary_hash=binary_hash,
        file_size_bytes=file_size,
        page_count=len(doc.pages) if hasattr(doc, 'pages') else 0,
        processing_time_ms=result.timings.get('total', 0) * 1000 if hasattr(result, 'timings') else None,
        parsed_at=datetime.utcnow()
    )
    return metadata


def extract_statistics(doc: Any) -> DocumentStatistics:
    """
    Extract document statistics

    Args:
        doc: Docling document object

    Returns:
        DocumentStatistics object
    """
    stats = DocumentStatistics(
        total_text_items=len(doc.texts) if hasattr(doc, 'texts') else 0,
        total_tables=len(doc.tables) if hasattr(doc, 'tables') else 0,
        total_pictures=len(doc.pictures) if hasattr(doc, 'pictures') else 0,
        total_key_value_items=len(doc.key_value_items) if hasattr(doc, 'key_value_items') else 0
    )
    return stats


def extract_pages(doc: Any) -> List[PageInfo]:
    """
    Extract page information

    Args:
        doc: Docling document object

    Returns:
        List of PageInfo objects
    """
    pages = []
    if not hasattr(doc, 'pages'):
        return pages

    for i, page in enumerate(doc.pages, 1):
        page_info = PageInfo(
            page_number=i,
            width=page.size.width if hasattr(page, 'size') else None,
            height=page.size.height if hasattr(page, 'size') else None
        )
        pages.append(page_info)

    return pages


def extract_texts(doc: Any) -> List[TextItem]:
    """
    Extract text items from document

    Args:
        doc: Docling document object

    Returns:
        List of TextItem objects
    """
    texts = []
    if not hasattr(doc, 'texts'):
        return texts

    for text_item in doc.texts:
        bbox = None
        page = None

        if hasattr(text_item, 'prov') and text_item.prov:
            page = text_item.prov[0].page_no
            if hasattr(text_item.prov[0], 'bbox'):
                bbox = BoundingBox(
                    left=text_item.prov[0].bbox.l,
                    top=text_item.prov[0].bbox.t,
                    right=text_item.prov[0].bbox.r,
                    bottom=text_item.prov[0].bbox.b
                )

        texts.append(TextItem(
            label=text_item.label if hasattr(text_item, 'label') else "unknown",
            text=text_item.text if hasattr(text_item, 'text') else "",
            page=page,
            bbox=bbox
        ))

    return texts


def extract_tables(doc: Any) -> List[TableItem]:
    """
    Extract tables from document

    Args:
        doc: Docling document object

    Returns:
        List of TableItem objects
    """
    tables = []
    if not hasattr(doc, 'tables'):
        return tables

    for table in doc.tables:
        # Export to dict
        table_dict = table.export_to_dict() if hasattr(table, 'export_to_dict') else {}

        # Try to export to DataFrame and CSV
        dataframe_csv = None
        rows = None
        columns = None

        try:
            df = table.export_to_dataframe()
            if df is not None:
                rows = df.shape[0]
                columns = df.shape[1]
                dataframe_csv = df.to_csv(index=False)
        except Exception as e:
            print(f"Warning: Could not export table to DataFrame: {e}")

        # Get page info
        page = None
        if hasattr(table, 'prov') and table.prov:
            page = table.prov[0].page_no

        tables.append(TableItem(
            id=table.self_ref if hasattr(table, 'self_ref') else f"table-{len(tables)+1}",
            page=page,
            rows=rows,
            columns=columns,
            data=table_dict,
            dataframe_csv=dataframe_csv
        ))

    return tables


def extract_pictures(doc: Any) -> List[PictureItem]:
    """
    Extract pictures/images from document

    Args:
        doc: Docling document object

    Returns:
        List of PictureItem objects
    """
    pictures = []
    if not hasattr(doc, 'pictures'):
        return pictures

    for picture in doc.pictures:
        # Extract basic info
        page = None
        bbox = None
        caption = None
        image_uri = None

        # Get page and bbox
        if hasattr(picture, 'prov') and picture.prov:
            page = picture.prov[0].page_no
            if hasattr(picture.prov[0], 'bbox'):
                bbox = BoundingBox(
                    left=picture.prov[0].bbox.l,
                    top=picture.prov[0].bbox.t,
                    right=picture.prov[0].bbox.r,
                    bottom=picture.prov[0].bbox.b
                )

        # Get caption
        if hasattr(picture, 'caption_text'):
            try:
                caption = picture.caption_text(doc=doc)
            except Exception:
                pass

        # Get image URI
        if hasattr(picture, 'image') and picture.image:
            image_uri = str(picture.image.uri)

        pictures.append(PictureItem(
            id=picture.self_ref if hasattr(picture, 'self_ref') else f"picture-{len(pictures)+1}",
            page=page,
            bbox=bbox,
            caption=caption,
            image_uri=image_uri
        ))

    return pictures


def generate_job_id() -> str:
    """Generate unique job ID"""
    return str(uuid.uuid4())


# ============================================================================
# IMAGE DESCRIPTION UTILITIES
# ============================================================================

def describe_image_with_gemini(image_uri: str, prompt: str, api_key: str) -> Optional[str]:
    """
    Generate image description using Google Gemini (native SDK)
    Based on working implementation from image_description_gemini.py

    Args:
        image_uri: Base64 data URI of the image (format: data:image/png;base64,...)
        prompt: Description prompt
        api_key: Gemini API key

    Returns:
        Description text or None if failed
    """
    try:
        import google.generativeai as genai
        import base64
        import re
        from io import BytesIO
        import PIL.Image
    except ImportError:
        print("Warning: google-generativeai or PIL not installed. Cannot use Gemini.")
        return None

    try:
        # Configure Gemini API (same as working version)
        genai.configure(api_key=api_key)

        # Create model (same as working version)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Extract base64 data from data URI
        # Format: data:image/png;base64,<base64_data>
        if not image_uri.startswith('data:image/'):
            print(f"Warning: Invalid image URI format")
            return None

        match = re.match(r'data:image/\w+;base64,(.+)', image_uri)
        if not match:
            print(f"Warning: Could not parse data URI")
            return None

        image_base64 = match.group(1)
        image_data = base64.b64decode(image_base64)

        # Prepare image (exactly like working version)
        image = PIL.Image.open(BytesIO(image_data))

        # Generate description (exactly like working version)
        response = model.generate_content([prompt, image])

        return response.text.strip()

    except Exception as e:
        print(f"Warning: Gemini description failed: {e}")
        return f"Error: {str(e)}"


def describe_image_with_openai(image_uri: str, prompt: str, api_key: str) -> Optional[str]:
    """
    Generate image description using OpenAI GPT-4 Vision via LangChain

    Args:
        image_uri: Base64 data URI of the image
        prompt: Description prompt
        api_key: OpenAI API key

    Returns:
        Description text or None if failed
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("Warning: langchain-openai not installed. Cannot use OpenAI.")
        return None

    try:
        # Create OpenAI vision model
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0
        )

        # Create message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_uri}}
                ]
            }
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        print(f"Warning: OpenAI description failed: {e}")
        return None
