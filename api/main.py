"""
Docling Document Parser REST API
FastAPI application with complete document parsing endpoints
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from typing import Optional
import json

from config import settings
from models import (
    ParsingMode, JobStatus, ParseOptions,
    JobCreatedResponse, JobStatusResponse, ParseResultResponse,
    TextsResponse, TablesResponse, ImagesResponse,
    ErrorResponse, ExportFormat, ImageDescriptionProvider
)
from storage import job_storage
from utils import validate_file, save_upload_file, generate_job_id
from parser import parse_document_task


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS - Root
# ============================================================================

@app.get(
    "/",
    include_in_schema=False,
    tags=["System"]
)
async def root():
    """
    Root endpoint - redirects to API documentation.
    """
    return RedirectResponse(url="/docs")


# ============================================================================
# ENDPOINTS - Main Parsing
# ============================================================================

@app.post(
    "/api/v1/parse/document",
    response_model=JobCreatedResponse,
    status_code=202,
    tags=["Document Parsing"],
    summary="Upload and parse a document",
    description="Upload a document (PDF, DOCX, etc.) for parsing. Returns a job ID to check status and retrieve results."
)
async def parse_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to parse"),
    parsing_mode: ParsingMode = Query(
        default=ParsingMode.STANDARD,
        description="Parsing mode: standard, ocr, fast, or high_quality"
    ),
    extract_images: bool = Query(
        default=True,
        description="Extract images from document"
    ),
    extract_tables: bool = Query(
        default=True,
        description="Extract tables from document"
    ),
    images_scale: float = Query(
        default=2.0,
        ge=1.0,
        le=4.0,
        description="Image quality scale (1.0-4.0)"
    ),
    describe_images: bool = Query(
        default=False,
        description="Generate AI descriptions for images"
    ),
    description_provider: ImageDescriptionProvider = Query(
        default=ImageDescriptionProvider.NONE,
        description="Provider for image descriptions: none, docling (SmolVLM), gemini, or openai"
    ),
    description_prompt: Optional[str] = Query(
        default=None,
        description="Custom prompt for image descriptions (optional)"
    )
):
    """
    Upload a document for parsing.

    Supported formats:
    - PDF (.pdf)
    - Word (.docx, .doc)
    - HTML (.html)
    - Markdown (.md)
    - Images (.png, .jpg, .tiff) - with OCR mode

    Returns a job ID to track processing status.
    """
    # Validate file
    content_type = validate_file(file)

    # Generate job ID
    job_id = generate_job_id()

    # Save uploaded file
    file_path = await save_upload_file(file, job_id)

    # Prepare parsing options
    options = {
        "extract_images": extract_images,
        "extract_tables": extract_tables,
        "images_scale": images_scale,
        "describe_images": describe_images,
        "description_provider": description_provider,
        "description_prompt": description_prompt
    }

    # Create job record
    job_storage.create_job(
        job_id=job_id,
        filename=file.filename,
        file_path=str(file_path),
        parsing_mode=parsing_mode.value,
        options=options
    )

    # Queue background parsing task
    background_tasks.add_task(
        parse_document_task,
        job_id=job_id,
        file_path=file_path,
        parsing_mode=parsing_mode,
        options=options
    )

    return JobCreatedResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        status_url=f"/api/v1/parse/jobs/{job_id}",
        estimated_time_seconds=30
    )


# ============================================================================
# ENDPOINTS - Job Status
# ============================================================================

@app.get(
    "/api/v1/parse/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Job Management"],
    summary="Check job status",
    description="Check the processing status of a parsing job"
)
async def get_job_status(job_id: str):
    """
    Check the status of a parsing job.

    Returns:
    - Job status (pending, processing, completed, failed)
    - Progress percentage
    - Result URL (if completed)
    - Error message (if failed)
    """
    job = job_storage.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "JOB_NOT_FOUND",
                "message": f"Job with ID '{job_id}' not found"
            }
        )

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress_percent=job.get("progress_percent"),
        result_url=f"/api/v1/parse/results/{job_id}" if job["status"] == JobStatus.COMPLETED else None,
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


# ============================================================================
# ENDPOINTS - Results Retrieval
# ============================================================================

@app.get(
    "/api/v1/parse/results/{job_id}",
    response_model=ParseResultResponse,
    tags=["Results"],
    summary="Get complete parsing results",
    description="Retrieve complete parsing results including metadata, texts, tables, and images"
)
async def get_results(job_id: str):
    """
    Get complete parsing results for a job.

    Returns all extracted data:
    - Document metadata
    - Statistics
    - Full markdown content
    - Text items with labels and positions
    - Tables with data
    - Images with captions
    """
    result = job_storage.get_result(job_id)

    if not result:
        # Check if job exists
        job = job_storage.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "JOB_NOT_FOUND",
                    "message": f"Job with ID '{job_id}' not found"
                }
            )

        # Job exists but result not ready or expired
        if job["status"] == JobStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "PARSING_FAILED",
                    "message": job.get("error_message", "Document parsing failed")
                }
            )
        elif job["status"] in [JobStatus.PENDING, JobStatus.PROCESSING]:
            raise HTTPException(
                status_code=202,
                detail={
                    "error": "PROCESSING",
                    "message": "Document is still being processed",
                    "status_url": f"/api/v1/parse/jobs/{job_id}"
                }
            )
        else:
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "RESULT_EXPIRED",
                    "message": "Results have expired and are no longer available"
                }
            )

    return ParseResultResponse(**result)


# ============================================================================
# ENDPOINTS - Filtered Data
# ============================================================================

@app.get(
    "/api/v1/parse/results/{job_id}/texts",
    response_model=TextsResponse,
    tags=["Results"],
    summary="Get text items",
    description="Get text items, optionally filtered by page or label"
)
async def get_texts(
    job_id: str,
    page: Optional[int] = Query(None, description="Filter by page number"),
    label: Optional[str] = Query(None, description="Filter by label (title, paragraph, etc.)")
):
    """
    Get text items from parsed document.

    Optionally filter by:
    - page: Page number
    - label: Text label (title, paragraph, section_header, etc.)
    """
    result = job_storage.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    texts = result["content"]["texts"]

    # Apply filters
    if page is not None:
        texts = [t for t in texts if t.get("page") == page]

    if label is not None:
        texts = [t for t in texts if t.get("label") == label]

    return TextsResponse(
        texts=texts,
        count=len(texts),
        page_filter=page,
        label_filter=label
    )


@app.get(
    "/api/v1/parse/results/{job_id}/tables",
    response_model=TablesResponse,
    tags=["Results"],
    summary="Get tables",
    description="Get extracted tables in various formats"
)
async def get_tables(
    job_id: str,
    format: ExportFormat = Query(
        default=ExportFormat.DICT,
        description="Output format (dict or csv)"
    )
):
    """
    Get tables from parsed document.

    Format options:
    - dict: Table data as nested dictionary
    - csv: Table data as CSV string
    """
    result = job_storage.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    tables = result["content"]["tables"]

    # Format tables based on requested format
    if format == ExportFormat.CSV:
        # Return only CSV data
        formatted_tables = []
        for table in tables:
            formatted_tables.append({
                "id": table["id"],
                "page": table.get("page"),
                "csv": table.get("dataframe_csv", "")
            })
        tables = formatted_tables

    return TablesResponse(
        tables=tables,
        count=len(tables),
        format=format.value
    )


@app.get(
    "/api/v1/parse/results/{job_id}/images",
    response_model=ImagesResponse,
    tags=["Results"],
    summary="Get images",
    description="Get extracted images with metadata"
)
async def get_images(job_id: str):
    """
    Get images from parsed document.

    Includes:
    - Image ID and page number
    - Bounding box coordinates
    - Caption (if available)
    - Image data as base64 URI
    """
    result = job_storage.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    pictures = result["content"]["pictures"]

    return ImagesResponse(
        images=pictures,
        count=len(pictures)
    )


# ============================================================================
# ENDPOINTS - Export Formats
# ============================================================================

@app.get(
    "/api/v1/parse/results/{job_id}/export/markdown",
    response_class=PlainTextResponse,
    tags=["Export"],
    summary="Export as Markdown",
    description="Get document as plain markdown text"
)
async def export_markdown(job_id: str):
    """
    Export document as markdown text.

    Returns plain text markdown representation of the document.
    """
    result = job_storage.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    return result["content"]["markdown"]


@app.get(
    "/api/v1/parse/results/{job_id}/export/json",
    tags=["Export"],
    summary="Export as JSON",
    description="Get complete document data as JSON"
)
async def export_json(job_id: str):
    """
    Export complete document data as JSON.

    Includes all metadata, statistics, texts, tables, and images.
    """
    result = job_storage.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    return JSONResponse(content=result)


# ============================================================================
# ENDPOINTS - Health & Info
# ============================================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Check API health status"
)
async def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION
    }


@app.get(
    "/api/v1/info",
    tags=["System"],
    summary="API information",
    description="Get API configuration and supported formats"
)
async def get_info():
    """
    Get API information and capabilities.

    Returns:
    - Supported file types
    - Parsing modes
    - Configuration limits
    """
    return {
        "api_version": settings.API_VERSION,
        "supported_mime_types": list(settings.SUPPORTED_MIME_TYPES.keys()),
        "supported_extensions": settings.ALLOWED_EXTENSIONS,
        "parsing_modes": [mode.value for mode in ParsingMode],
        "limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "result_ttl_seconds": settings.RESULTS_TTL_SECONDS,
            "job_timeout_seconds": settings.JOB_TIMEOUT_SECONDS
        }
    }


# ============================================================================
# ENDPOINTS - Job Management
# ============================================================================

@app.get(
    "/api/v1/jobs",
    tags=["Job Management"],
    summary="List all jobs",
    description="Get list of all jobs with optional status filter"
)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status")
):
    """
    List all jobs, optionally filtered by status.
    """
    jobs = job_storage.get_all_jobs(status=status)

    return {
        "jobs": jobs,
        "count": len(jobs),
        "status_filter": status.value if status else None
    }


# ============================================================================
# Application Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"Docs available at: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down API...")


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
