"""
Docling document parser implementation
Handles document conversion and data extraction
"""
import os
import time
from pathlib import Path
from typing import Dict, Any

# Disable symlinks for Windows compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from models import (
    ParsingMode, JobStatus, DocumentContent,
    ParseResultResponse, DocumentMetadata, ImageDescriptionProvider
)
from utils import (
    extract_metadata, extract_statistics, extract_pages,
    extract_texts, extract_tables, extract_pictures, cleanup_job_files,
    describe_image_with_gemini, describe_image_with_openai
)
from storage import job_storage
from config import settings


class DocumentParser:
    """
    Docling document parser with support for multiple parsing modes
    """

    def __init__(self):
        self.converter = None

    def _configure_pipeline_options(self, parsing_mode: ParsingMode,
                                   options: Dict[str, Any]) -> PdfPipelineOptions:
        """
        Configure PDF pipeline options based on parsing mode and custom options

        Args:
            parsing_mode: Parsing mode (standard, ocr, fast, high_quality)
            options: Custom parsing options

        Returns:
            Configured PdfPipelineOptions
        """
        pipeline_options = PdfPipelineOptions()

        # Image extraction settings
        if options.get("extract_images", settings.DEFAULT_EXTRACT_IMAGES):
            pipeline_options.generate_picture_images = True
            pipeline_options.images_scale = options.get(
                "images_scale",
                settings.DEFAULT_IMAGE_SCALE
            )

        # Image description settings (Docling VLM only)
        if options.get("describe_images", False):
            provider = options.get("description_provider", ImageDescriptionProvider.NONE)

            if provider == ImageDescriptionProvider.DOCLING:
                # Enable Docling's built-in VLM (SmolVLM)
                pipeline_options.do_picture_description = True
                from docling.datamodel.pipeline_options import smolvlm_picture_description
                pipeline_options.picture_description_options = smolvlm_picture_description

                # Set custom prompt if provided
                if options.get("description_prompt"):
                    pipeline_options.picture_description_options.prompt = options["description_prompt"]

        # Mode-specific configurations
        if parsing_mode == ParsingMode.OCR:
            # OCR mode - force OCR for all pages
            pipeline_options.do_ocr = True
            pipeline_options.ocr_engine = "easyocr"  # or "tesseract"

        elif parsing_mode == ParsingMode.FAST:
            # Fast mode - minimal processing
            pipeline_options.generate_picture_images = False
            pipeline_options.do_table_structure = False

        elif parsing_mode == ParsingMode.HIGH_QUALITY:
            # High quality mode - maximum accuracy
            pipeline_options.generate_picture_images = True
            pipeline_options.images_scale = 3.0
            pipeline_options.do_table_structure = True

        # Standard mode uses defaults

        return pipeline_options

    def _enrich_images_with_descriptions(self, pictures: list, options: Dict[str, Any]) -> list:
        """
        Add AI-generated descriptions to images using external providers

        Args:
            pictures: List of PictureItem dictionaries
            options: Parsing options with description settings

        Returns:
            List of PictureItem dictionaries with descriptions added
        """
        if not options.get("describe_images", False):
            return pictures

        provider = options.get("description_provider", ImageDescriptionProvider.NONE)

        if provider == ImageDescriptionProvider.NONE or provider == ImageDescriptionProvider.DOCLING:
            # No external descriptions needed
            return pictures

        # Get prompt (handle None values)
        prompt = options.get("description_prompt") or settings.DEFAULT_DESCRIPTION_PROMPT

        # Get API key
        if provider == ImageDescriptionProvider.GEMINI:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                print("Warning: GEMINI_API_KEY not set. Skipping image descriptions.")
                return pictures

        elif provider == ImageDescriptionProvider.OPENAI:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("Warning: OPENAI_API_KEY not set. Skipping image descriptions.")
                return pictures
        else:
            return pictures

        # Process each image
        enriched_pictures = []
        for picture in pictures:
            image_uri = picture.get("image_uri")

            if not image_uri:
                enriched_pictures.append(picture)
                continue

            # Generate description
            description = None
            try:
                if provider == ImageDescriptionProvider.GEMINI:
                    description = describe_image_with_gemini(image_uri, prompt, api_key)
                elif provider == ImageDescriptionProvider.OPENAI:
                    description = describe_image_with_openai(image_uri, prompt, api_key)

                if description:
                    picture["description"] = description
                    picture["description_provider"] = provider.value

            except Exception as e:
                print(f"Warning: Failed to describe image {picture.get('id')}: {e}")

            enriched_pictures.append(picture)

        return enriched_pictures

    def parse_document(self, job_id: str, file_path: Path,
                      parsing_mode: ParsingMode,
                      options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse document using Docling

        Args:
            job_id: Job identifier
            file_path: Path to document file
            parsing_mode: Parsing mode
            options: Custom parsing options

        Returns:
            Complete parsing result as dictionary
        """
        try:
            # Update job status
            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=10)

            # Configure pipeline
            pipeline_options = self._configure_pipeline_options(parsing_mode, options)

            # Initialize converter
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )

            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=30)

            # Convert document
            start_time = time.time()
            result = converter.convert(str(file_path))
            conversion_time = (time.time() - start_time) * 1000  # milliseconds

            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=60)

            # Extract document object
            doc = result.document

            # Get file size
            file_size = file_path.stat().st_size if file_path.exists() else None

            # Get original filename from job
            job_data = job_storage.get_job(job_id)
            filename = job_data.get("filename", file_path.name) if job_data else file_path.name

            # Extract all data
            metadata = extract_metadata(doc, result, filename, file_size)
            statistics = extract_statistics(doc)
            pages = extract_pages(doc)
            texts = extract_texts(doc)
            tables = extract_tables(doc)
            pictures = extract_pictures(doc)

            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=70)

            # Enrich images with AI descriptions if requested (Gemini/OpenAI)
            # Note: Docling descriptions are already included in extract_pictures
            pictures_dict = [pic.dict() if hasattr(pic, 'dict') else pic for pic in pictures]
            pictures_dict = self._enrich_images_with_descriptions(pictures_dict, options)

            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=80)

            # Export markdown
            markdown = doc.export_to_markdown() if hasattr(doc, 'export_to_markdown') else ""

            # Build content object
            content = DocumentContent(
                markdown=markdown,
                pages=pages,
                texts=texts,
                tables=tables,
                pictures=pictures_dict
            )

            job_storage.update_job_status(job_id, JobStatus.PROCESSING, progress_percent=90)

            # Build complete result
            result_data = {
                "job_id": job_id,
                "status": JobStatus.COMPLETED,
                "metadata": metadata.dict(),
                "statistics": statistics.dict(),
                "content": content.dict(),
                "exports": {
                    "markdown_url": f"/api/v1/parse/results/{job_id}/export/markdown",
                    "json_url": f"/api/v1/parse/results/{job_id}/export/json",
                    "images_url": f"/api/v1/parse/results/{job_id}/images" if pictures_dict else None
                }
            }

            # Store result
            job_storage.store_result(job_id, result_data)

            # Update job status to completed
            job_storage.update_job_status(job_id, JobStatus.COMPLETED, progress_percent=100)

            return result_data

        except Exception as e:
            # Update job status to failed
            error_message = f"Parsing failed: {str(e)}"
            job_storage.update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=error_message
            )
            raise

        finally:
            # Cleanup temporary files
            cleanup_job_files(job_id)


# Global parser instance
document_parser = DocumentParser()


def parse_document_task(job_id: str, file_path: Path,
                       parsing_mode: ParsingMode,
                       options: Dict[str, Any]):
    """
    Background task to parse document

    Args:
        job_id: Job identifier
        file_path: Path to document file
        parsing_mode: Parsing mode
        options: Custom parsing options
    """
    try:
        document_parser.parse_document(job_id, file_path, parsing_mode, options)
    except Exception as e:
        print(f"Error parsing document for job {job_id}: {e}")
        # Error already handled in parse_document
