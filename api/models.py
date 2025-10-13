"""
Pydantic models for API request/response schemas
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class ParsingMode(str, Enum):
    """Available parsing modes"""
    STANDARD = "standard"
    OCR = "ocr"
    FAST = "fast"
    HIGH_QUALITY = "high_quality"


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Export format options"""
    JSON = "json"
    MARKDOWN = "markdown"
    CSV = "csv"
    DICT = "dict"


class ImageDescriptionProvider(str, Enum):
    """Image description provider options"""
    NONE = "none"  # No image descriptions
    DOCLING = "docling"  # Use Docling's built-in VLM (SmolVLM)
    GEMINI = "gemini"  # Use Google Gemini API
    OPENAI = "openai"  # Use OpenAI GPT-4o Vision (future)


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ParseOptions(BaseModel):
    """Optional parsing configuration"""
    extract_images: bool = Field(default=True, description="Extract images from document")
    extract_tables: bool = Field(default=True, description="Extract tables from document")
    images_scale: float = Field(default=2.0, ge=1.0, le=4.0, description="Image quality scale")
    language: Optional[str] = Field(default="en", description="Document language for OCR")

    # Image description options
    describe_images: bool = Field(default=False, description="Generate AI descriptions for images")
    description_provider: ImageDescriptionProvider = Field(
        default=ImageDescriptionProvider.NONE,
        description="Provider for image descriptions (none, docling, gemini, openai)"
    )
    description_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for image descriptions (optional)"
    )


# ============================================================================
# RESPONSE MODELS - Job Management
# ============================================================================

class JobCreatedResponse(BaseModel):
    """Response when a parsing job is created"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    status_url: str = Field(..., description="URL to check job status")
    estimated_time_seconds: Optional[int] = Field(None, description="Estimated processing time")


class JobStatusResponse(BaseModel):
    """Response for job status check"""
    job_id: str
    status: JobStatus
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# RESPONSE MODELS - Document Content
# ============================================================================

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    left: float
    top: float
    right: float
    bottom: float


class TextItem(BaseModel):
    """Extracted text item with metadata"""
    label: str = Field(..., description="Text type (title, paragraph, section_header, etc.)")
    text: str = Field(..., description="Extracted text content")
    page: Optional[int] = Field(None, description="Page number")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")


class TableItem(BaseModel):
    """Extracted table with data"""
    id: str = Field(..., description="Table reference ID")
    page: Optional[int] = Field(None, description="Page number")
    rows: Optional[int] = Field(None, description="Number of rows")
    columns: Optional[int] = Field(None, description="Number of columns")
    data: Dict[str, Any] = Field(..., description="Table data as dictionary")
    dataframe_csv: Optional[str] = Field(None, description="Table as CSV string")


class PictureItem(BaseModel):
    """Extracted picture/image with metadata"""
    id: str = Field(..., description="Picture reference ID")
    page: Optional[int] = Field(None, description="Page number")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")
    caption: Optional[str] = Field(None, description="Image caption")
    image_uri: Optional[str] = Field(None, description="Image data URI (base64)")
    description: Optional[str] = Field(None, description="AI-generated image description")
    description_provider: Optional[str] = Field(None, description="Provider used for description")


class PageInfo(BaseModel):
    """Page metadata"""
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    items_count: Optional[int] = None


class DocumentMetadata(BaseModel):
    """Document metadata and statistics"""
    filename: str
    mimetype: Optional[str] = None
    binary_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: int
    processing_time_ms: Optional[float] = None
    parsed_at: datetime


class DocumentStatistics(BaseModel):
    """Document content statistics"""
    total_text_items: int
    total_tables: int
    total_pictures: int
    total_key_value_items: int = 0


class DocumentContent(BaseModel):
    """Complete document content"""
    markdown: str = Field(..., description="Full document as markdown")
    pages: List[PageInfo] = Field(default_factory=list)
    texts: List[TextItem] = Field(default_factory=list)
    tables: List[TableItem] = Field(default_factory=list)
    pictures: List[PictureItem] = Field(default_factory=list)


class ExportUrls(BaseModel):
    """URLs for different export formats"""
    markdown_url: str
    json_url: str
    images_url: Optional[str] = None


class ParseResultResponse(BaseModel):
    """Complete parsing result"""
    job_id: str
    status: JobStatus
    metadata: DocumentMetadata
    statistics: DocumentStatistics
    content: DocumentContent
    exports: ExportUrls


# ============================================================================
# RESPONSE MODELS - Filtered Data
# ============================================================================

class TextsResponse(BaseModel):
    """Response for texts endpoint"""
    texts: List[TextItem]
    count: int
    page_filter: Optional[int] = None
    label_filter: Optional[str] = None


class TablesResponse(BaseModel):
    """Response for tables endpoint"""
    tables: List[TableItem]
    count: int
    format: str = "dict"


class ImagesResponse(BaseModel):
    """Response for images endpoint"""
    images: List[PictureItem]
    count: int


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Error response detail"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail
