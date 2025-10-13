# Agentic Architecture for Document Parser API

## Overview

This document describes the conceptual architecture for transforming the Docling Document Parser REST API into an intelligent agentic system using **FastAPI-MCP** and **LangGraph**.

The goal is to enable natural language interactions where users can simply describe what they want (e.g., "Parse this PDF with Gemini image descriptions and show me the tables") and the system automatically figures out which tools to call, manages async operations, and returns the desired results.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layer 1: FastAPI to MCP Server](#layer-1-fastapi-to-mcp-server)
3. [Layer 2: LangGraph Agent](#layer-2-langgraph-agent)
4. [The Agentic Flow](#the-agentic-flow)
5. [Key Concepts](#key-concepts)
6. [File Upload Strategies](#file-upload-strategies)
7. [Implementation Patterns](#implementation-patterns)
8. [Multi-Agent Pattern](#multi-agent-pattern-advanced)
9. [Use Cases and Examples](#use-cases-and-examples)
10. [References and Resources](#references-and-resources)

---

## Architecture Overview

### What is MCP (Model Context Protocol)?

MCP is a standardized communication layer that enables AI agents (like Claude or GPT) to understand and interact with external APIs. It serves as the "language" that LLMs use to discover, understand, and invoke tools.

### What is LangGraph?

LangGraph is a graph-based orchestration framework for building production-ready agentic systems. Unlike simple tool-calling chains, LangGraph models agents as **stateful graphs** with:
- Memory persistence across interactions
- Complex control flows (loops, conditionals, parallel execution)
- Human-in-the-loop capabilities
- Durable execution with automatic recovery

### The Two-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  User: "Parse this PDF and show me the images"     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│           LAYER 2: LangGraph Agent                  │
│  • Understands natural language intent              │
│  • Plans multi-step workflows                       │
│  • Manages state and memory                         │
│  • Handles async operations                         │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼ (Calls MCP Tools)
┌─────────────────────────────────────────────────────┐
│           LAYER 1: MCP Server                       │
│  • Exposes FastAPI endpoints as MCP tools           │
│  • Preserves OpenAPI schemas                        │
│  • Maintains authentication/security                │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│      Your Existing FastAPI Application             │
│  • /api/v1/parse/document                          │
│  • /api/v1/parse/jobs/{job_id}                     │
│  • /api/v1/parse/results/{job_id}                  │
│  • /api/v1/parse/results/{job_id}/texts            │
│  • /api/v1/parse/results/{job_id}/images           │
│  • etc...                                          │
└─────────────────────────────────────────────────────┘
```

---

## Layer 1: FastAPI to MCP Server

### Transformation with FastAPI-MCP

Using the **FastAPI-MCP** library (github.com/tadata-org/fastapi_mcp), your REST endpoints automatically become MCP tools with **zero or minimal configuration**.

### How It Works

**Before (REST API):**
```
POST /api/v1/parse/document
  - file: UploadFile
  - parsing_mode: standard|ocr|fast|high_quality
  - extract_images: bool
  - describe_images: bool
  - description_provider: none|docling|gemini|openai
```

**After (MCP Tool):**
```json
{
  "name": "parse_document",
  "description": "Upload and parse a document (PDF, DOCX, etc.) for parsing...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file": { "type": "string", "description": "Document file to parse" },
      "parsing_mode": {
        "type": "string",
        "enum": ["standard", "ocr", "fast", "high_quality"],
        "default": "standard"
      },
      "extract_images": { "type": "boolean", "default": true },
      "describe_images": { "type": "boolean", "default": false },
      "description_provider": {
        "type": "string",
        "enum": ["none", "docling", "gemini", "openai"]
      }
    }
  }
}
```

### Key Benefits

1. **Schema Preservation**: Your Pydantic models become tool schemas
2. **Documentation Reuse**: FastAPI docstrings become tool descriptions
3. **Auth Maintained**: Security policies from FastAPI are preserved
4. **Zero Rewriting**: Your existing API code doesn't change

### Tool Inventory

Your API would expose approximately these MCP tools:

| Tool Name | Endpoint | Purpose |
|-----------|----------|---------|
| `parse_document` | POST /api/v1/parse/document | Upload and parse document |
| `get_job_status` | GET /api/v1/parse/jobs/{job_id} | Check parsing job status |
| `get_results` | GET /api/v1/parse/results/{job_id} | Get complete results |
| `get_texts` | GET /api/v1/parse/results/{job_id}/texts | Get text items (with filters) |
| `get_tables` | GET /api/v1/parse/results/{job_id}/tables | Get extracted tables |
| `get_images` | GET /api/v1/parse/results/{job_id}/images | Get extracted images |
| `export_markdown` | GET /api/v1/parse/results/{job_id}/export/markdown | Export as Markdown |
| `export_json` | GET /api/v1/parse/results/{job_id}/export/json | Export as JSON |
| `list_jobs` | GET /api/v1/jobs | List all jobs |
| `get_api_info` | GET /api/v1/info | Get API capabilities |

---

## Layer 2: LangGraph Agent

### The Graph Structure

LangGraph models the agent as a **state machine** with nodes and edges:

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Analyze Intent │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Plan Workflow  │
                  └────────┬────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
       ┌─────────────────┐   ┌──────────────┐
       │  Execute Tools  │   │ Check State  │
       └────────┬────────┘   └──────┬───────┘
                │                   │
                │◄──────────────────┘
                │ (Loop if needed)
                │
                ▼
         ┌─────────────────┐
         │ Format Response │
         └────────┬────────┘
                  │
                  ▼
             ┌─────────┐
             │   END   │
             └─────────┘
```

### Node Types

**1. Planning Node**
- Analyzes user's natural language request
- Identifies required tools and parameters
- Creates execution plan

**2. Tool Execution Nodes**
- Calls MCP tools (your API endpoints)
- Handles responses and errors
- Updates state with results

**3. Decision Nodes**
- Checks if goal is achieved
- Determines next steps
- Routes to appropriate nodes

**4. Memory Node**
- Stores job IDs, file references
- Tracks processing status
- Maintains conversation context

**5. Human-in-the-Loop Node**
- Pauses for user approval
- Requests clarification
- Awaits confirmation for expensive operations

**6. Polling/Wait Node**
- Monitors async job status
- Implements exponential backoff
- Handles long-running operations

---

## The Agentic Flow

### Example: Parse and Extract Tables

**User Request:**
```
"Parse this PDF with Gemini image descriptions and show me the extracted tables"
```

**Agent's Reasoning and Execution:**

```
Step 1: Intent Analysis
├─ Primary Goal: Parse document
├─ Configuration: Gemini image descriptions
└─ Secondary Goal: Retrieve tables

Step 2: Tool Planning
├─ Tool 1: parse_document(file_ref, description_provider="gemini")
├─ Tool 2: Monitor job status (polling loop)
└─ Tool 3: get_tables(job_id) when complete

Step 3: Execution
│
├─ Call parse_document()
│  └─ Returns: { "job_id": "abc-123", "status": "pending" }
│  └─ Store in memory: job_id = "abc-123"
│
├─ Enter polling loop:
│  ├─ Call get_job_status(job_id="abc-123")
│  ├─ Status: "processing" (60% complete)
│  ├─ Wait 5 seconds
│  ├─ Call get_job_status(job_id="abc-123")
│  └─ Status: "completed" ✓
│
├─ Call get_tables(job_id="abc-123")
│  └─ Returns: { "tables": [...], "count": 3 }
│
└─ Format and present results to user

Step 4: Response
"I've parsed your document with Gemini image descriptions.
Found 3 tables:

Table 1: Financial Summary (page 2)
[table data...]

Table 2: Product Comparison (page 5)
[table data...]

Table 3: Quarterly Results (page 8)
[table data...]"
```

### Example: Complex Multi-Step Request

**User Request:**
```
"Parse document.pdf with OCR, then if there are more than 10 images,
use Gemini descriptions, otherwise skip it. Show me only images from page 3."
```

**Agent's Reasoning:**

```
Step 1: Parse with OCR mode
├─ Call parse_document(mode="ocr", describe_images=false)
└─ Store job_id in memory

Step 2: Wait for completion
└─ Poll until status = "completed"

Step 3: Check image count
├─ Call get_results(job_id)
├─ Count images: 15 found
└─ Decision: > 10, need descriptions

Step 4: Re-process with descriptions
├─ Parse same file again with describe_images=true, provider="gemini"
├─ Wait for completion
└─ Get new results

Step 5: Filter and return
├─ Call get_images(job_id)
├─ Filter: page == 3
└─ Return filtered results
```

---

## Key Concepts

### 1. Stateful Memory

The agent maintains **persistent state** across interactions:

```python
State = {
    "conversation_history": [...],
    "active_jobs": {
        "job_abc123": {
            "status": "processing",
            "filename": "report.pdf",
            "created_at": "2025-01-15T10:30:00"
        }
    },
    "uploaded_files": {
        "file_xyz789": "/temp/uploads/document.pdf"
    },
    "user_preferences": {
        "default_mode": "standard",
        "preferred_image_provider": "gemini"
    }
}
```

**Benefits:**
- Reference "that document" or "the last job"
- Track multiple concurrent parsing jobs
- Resume conversations after interruptions
- Learn user preferences over time

### 2. Dynamic Routing

The agent **intelligently routes** based on context:

```python
if user_says("show me"):
    # Route to retrieval path
    if "images" in query:
        route_to(get_images_node)
    elif "tables" in query:
        route_to(get_tables_node)
    elif "text" in query:
        route_to(get_texts_node)

elif user_says("parse"):
    # Route to parsing path
    route_to(parse_document_node)

elif job_status == "processing":
    # Route to monitoring path
    route_to(poll_job_status_node)
```

### 3. Autonomous Loops

The agent handles **long-running operations** autonomously:

```python
def polling_node(state):
    job_id = state["current_job_id"]

    while True:
        status = call_tool("get_job_status", job_id=job_id)

        if status["status"] == "completed":
            state["job_completed"] = True
            return state  # Exit loop

        elif status["status"] == "failed":
            state["error"] = status["error_message"]
            return state  # Exit with error

        else:
            # Still processing, wait and retry
            sleep(exponential_backoff())
            continue
```

### 4. Human-in-the-Loop

The agent can **pause for human input**:

```python
def confirmation_node(state):
    image_count = state["image_count"]
    estimated_cost = image_count * 0.01  # $0.01 per image

    if estimated_cost > 5.0:
        # Expensive operation, ask for approval
        response = request_human_input(
            f"About to describe {image_count} images with Gemini API. "
            f"Estimated cost: ${estimated_cost:.2f}. Continue?"
        )

        if response.lower() == "yes":
            state["approved"] = True
            return route_to(describe_images_node)
        else:
            state["approved"] = False
            return route_to(skip_descriptions_node)
    else:
        # Cheap operation, proceed automatically
        state["approved"] = True
        return route_to(describe_images_node)
```

**Key feature**: Unlike websocket-based systems, LangGraph can wait **hours or days** for human response while persisting state.

### 5. Tool Composition

The agent **chains multiple tools** intelligently:

**Example: "Show me all figure captions from the document"**

```python
# Agent's reasoning:
# 1. Need to get images (which contain captions)
# 2. Filter only figure-type images
# 3. Extract just the captions

results = call_tool("get_images", job_id=job_id)
figures = [img for img in results if "figure" in img.get("caption", "").lower()]
captions = [fig["caption"] for fig in figures if fig["caption"]]

return format_response(captions)
```

### 6. Error Recovery

The agent handles **failures gracefully**:

```python
def parse_with_retry(state, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = call_tool("parse_document", **params)
            return result

        except TimeoutError:
            if attempt < max_retries - 1:
                wait(backoff_time)
                continue
            else:
                return route_to(error_handler_node)

        except AuthenticationError:
            # Don't retry auth errors
            return route_to(auth_error_node)
```

---

## File Upload Strategies

### Challenge

MCP tools operate on **text-based parameters**, but document parsing requires **binary files**. How do we bridge this gap?

### Approach 1: File Path Reference ⭐ Simplest

**Concept:**
- User uploads file to a local folder/cloud storage **before** interacting with agent
- Agent receives just the **file path** as text
- Tool accesses file directly from path

**User Flow:**
```
1. User: Uploads "report.pdf" to /uploads/ folder
2. User: "Parse /uploads/report.pdf with Gemini descriptions"
3. Agent: Calls parse_document(file_path="/uploads/report.pdf", provider="gemini")
```

**Pros:**
- Simple implementation
- No size limits
- No encoding overhead

**Cons:**
- Requires separate upload step
- File must be accessible to server
- Manual path entry

**Best for:** Local deployments, internal tools, batch processing

---

### Approach 2: Base64 Encoding

**Concept:**
- Files get **base64 encoded** into text strings
- Encoded content passed directly in tool parameters
- Tool decodes and processes

**User Flow:**
```
1. User: Attaches file in UI
2. System: Converts to base64 string
3. Agent: Calls parse_document(file_content="data:application/pdf;base64,JVBERi0x...")
```

**Pros:**
- Self-contained (no external storage)
- Works with any MCP-compatible client
- Simple for small files

**Cons:**
- 33% size increase from encoding
- Size limits (~5-10MB practical limit)
- Slower for large files
- High memory usage

**Best for:** Small documents, demos, simple integrations

---

### Approach 3: Presigned URLs ⭐ Production Standard

**Concept:**
- User uploads to **cloud storage** (S3, Azure Blob, GCS)
- Gets back a **temporary/presigned URL** (expires after 1 hour)
- Agent downloads file from URL for processing

**User Flow:**
```
1. User: Uploads file to S3
2. System: Returns presigned URL: https://bucket.s3.aws/temp/doc.pdf?sig=abc&expires=3600
3. User: "Parse https://bucket.s3.aws/temp/doc.pdf?sig=abc&expires=3600"
4. Agent: Downloads file → Processes → Deletes
```

**Pros:**
- Handles any file size
- Secure (time-limited URLs)
- Scalable for production
- No server storage needed

**Cons:**
- Requires cloud storage setup
- Additional infrastructure cost
- URL expiration to manage

**Best for:** Production systems, large files, public APIs

---

### Approach 4: Two-Step Tool Pattern ⭐ Most Practical

**Concept:**
Split upload and processing into **two separate MCP tools**:

**Tool 1: `upload_document`**
```json
{
  "name": "upload_document",
  "parameters": {
    "file_content": "base64_encoded_data",
    "filename": "report.pdf"
  },
  "returns": {
    "upload_id": "temp_xyz123",
    "expires_at": "2025-01-15T12:00:00"
  }
}
```

**Tool 2: `parse_document`**
```json
{
  "name": "parse_document",
  "parameters": {
    "upload_id": "temp_xyz123",  # Reference from upload
    "parsing_mode": "standard",
    "description_provider": "gemini"
  }
}
```

**Agent Flow:**
```
User: "Parse my report with Gemini"

Agent's plan:
1. Call upload_document(file_content=<base64>)
   → upload_id = "temp_xyz123"

2. Call parse_document(upload_id="temp_xyz123", provider="gemini")
   → job_id = "abc-def"

3. Poll job status until complete
4. Return results
```

**Pros:**
- Clean separation of concerns
- Reusable uploads (parse multiple times)
- Handles larger files (chunked upload possible)
- Better error handling

**Cons:**
- Requires two tool calls
- More complex agent logic

**Best for:** Most real-world scenarios, good balance of simplicity and capability

---

### Approach 5: Session Upload Context

**Concept:**
- Files uploaded through **separate UI/channel**
- Stored in **session context** with the agent
- Agent references "the file you uploaded" naturally

**User Flow:**
```
1. User: [Uploads report.pdf via web UI]
2. System: Stores in session with ID "file_abc"
3. User: "Parse the report I just uploaded"
4. Agent: Checks session → Finds "report.pdf" → Calls parse_document(session_file="file_abc")
```

**Pros:**
- Most natural conversation flow
- No need to repeat file information
- Supports "the document from earlier" references

**Cons:**
- Requires session management infrastructure
- Complex state synchronization
- Session expiration to handle

**Best for:** Conversational UIs, multi-turn workflows

---

### Approach 6: Streaming Upload

**Concept:**
- Special MCP tool accepts **chunked/streamed data**
- Agent coordinates multi-part upload
- For very large documents (100MB+)

**Flow:**
```
Agent creates upload session
→ Sends chunk 1
→ Sends chunk 2
→ ...
→ Finalizes upload
→ Gets file reference
```

**Pros:**
- Handles massive files
- Resumable uploads
- Progress tracking

**Cons:**
- Complex implementation
- Requires special MCP support
- Not all clients support streaming

**Best for:** Very large files (100MB+), unreliable networks

---

### Recommended Hybrid Approach

For your document parser API, use a **combination**:

#### Small Files (<10MB):
Use **Base64 encoding** directly in tool parameters:
```python
parse_document(
    file_content="data:application/pdf;base64,JVBERi0x...",
    filename="doc.pdf",
    parsing_mode="standard"
)
```

#### Large Files (>10MB):
Use **Two-step upload pattern**:
```python
# Step 1: Upload
upload_id = upload_document(file_path="/local/path/large_doc.pdf")

# Step 2: Parse
job_id = parse_document(
    upload_id=upload_id,
    parsing_mode="high_quality",
    describe_images=True
)
```

#### Production Deployment:
Add **Presigned URL support**:
```python
parse_document_from_url(
    url="https://bucket.s3.aws/temp/doc.pdf?sig=...",
    parsing_mode="standard"
)
```

---

## Implementation Patterns

### Pattern 1: Stateful Conversations

**State structure:**
```python
from typing import TypedDict

class AgentState(TypedDict):
    messages: list[str]          # Conversation history
    current_job_id: str | None   # Active parsing job
    uploaded_files: dict         # File references
    results_cache: dict          # Cached results
    user_preferences: dict       # Settings
```

**Usage:**
```python
# User's first message
state["current_job_id"] = parse_document(...)

# Later in conversation
User: "Is it done yet?"
Agent: Checks state["current_job_id"] → Calls get_job_status(...)

User: "Show me the images"
Agent: Uses state["current_job_id"] → Calls get_images(...)
```

---

### Pattern 2: Job Monitoring Loop

**Implementation:**
```python
def monitor_job_node(state):
    job_id = state["current_job_id"]
    max_wait = 300  # 5 minutes
    check_interval = 5  # seconds

    start_time = time.time()

    while time.time() - start_time < max_wait:
        status = call_tool("get_job_status", job_id=job_id)

        if status["status"] == "completed":
            state["job_completed"] = True
            state["result_url"] = status["result_url"]
            return route_to(retrieve_results_node)

        elif status["status"] == "failed":
            state["error"] = status["error_message"]
            return route_to(error_handler_node)

        else:
            # Still processing
            progress = status.get("progress_percent", 0)
            state["progress"] = progress
            time.sleep(check_interval)

    # Timeout
    state["error"] = "Job processing timeout"
    return route_to(timeout_handler_node)
```

---

### Pattern 3: Conditional Tool Selection

**Implementation:**
```python
def select_tools_node(state):
    user_query = state["messages"][-1]

    # Parse intent
    if "parse" in user_query.lower():
        # Extract parameters from natural language
        mode = extract_parsing_mode(user_query)  # Uses LLM
        use_gemini = "gemini" in user_query.lower()

        return route_to(
            parse_node,
            params={"mode": mode, "describe_images": use_gemini}
        )

    elif "show" in user_query.lower() or "get" in user_query.lower():
        if "image" in user_query.lower():
            return route_to(get_images_node)
        elif "table" in user_query.lower():
            return route_to(get_tables_node)
        elif "text" in user_query.lower():
            return route_to(get_texts_node)
        else:
            return route_to(get_all_results_node)

    else:
        return route_to(clarification_node)
```

---

### Pattern 4: Error Recovery

**Implementation:**
```python
def error_handler_node(state):
    error = state.get("error")

    if "timeout" in error.lower():
        # Job might still be processing
        return {
            "message": "Processing is taking longer than expected. I'll keep checking.",
            "action": "continue_monitoring"
        }

    elif "not found" in error.lower():
        # Job ID invalid
        return {
            "message": "I couldn't find that job. Let's start over.",
            "action": "reset_state"
        }

    elif "authentication" in error.lower():
        # API key issue
        return {
            "message": "API authentication failed. Please check your credentials.",
            "action": "request_auth"
        }

    else:
        # Generic error
        return {
            "message": f"An error occurred: {error}",
            "action": "request_retry"
        }
```

---

### Pattern 5: Results Filtering

**Implementation:**
```python
def filter_results_node(state):
    user_query = state["messages"][-1]
    job_id = state["current_job_id"]

    # Get all results
    full_results = call_tool("get_results", job_id=job_id)

    # Apply filters based on query
    if "page" in user_query:
        page_num = extract_number(user_query)
        if "image" in user_query:
            filtered = call_tool("get_images", job_id=job_id)
            filtered = [img for img in filtered if img["page"] == page_num]
        elif "text" in user_query:
            filtered = call_tool("get_texts", job_id=job_id, page=page_num)

    elif "type" in user_query or "label" in user_query:
        label = extract_label(user_query)  # e.g., "title", "paragraph"
        filtered = call_tool("get_texts", job_id=job_id, label=label)

    else:
        filtered = full_results

    state["filtered_results"] = filtered
    return route_to(format_response_node)
```

---

## Multi-Agent Pattern (Advanced)

### Concept

Instead of one monolithic agent, use **specialized agents** coordinated by a supervisor:

```
                    ┌──────────────┐
                    │  Supervisor  │
                    │    Agent     │
                    └───────┬──────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Parser     │ │  Analysis   │ │   Export    │
    │    Agent     │ │    Agent    │ │    Agent    │
    └──────────────┘ └─────────────┘ └─────────────┘
```

### Agent Responsibilities

**1. Parser Agent**
- Handles document upload and parsing
- Monitors job status
- Manages parsing configurations

**Tools:**
- `parse_document`
- `get_job_status`
- `list_jobs`

---

**2. Analysis Agent**
- Queries and filters results
- Performs data analysis
- Generates summaries

**Tools:**
- `get_results`
- `get_texts`
- `get_tables`
- `get_images`

---

**3. Export Agent**
- Handles different export formats
- Manages file compression
- Coordinates downloads

**Tools:**
- `export_markdown`
- `export_json`
- (Future: `export_pdf`, `export_docx`)

---

**4. Supervisor Agent**
- Routes user requests to appropriate agent
- Coordinates multi-agent workflows
- Aggregates results

---

### Multi-Agent Flow Example

**User Request:**
```
"Parse this document, summarize the text, and export the tables as CSV"
```

**Supervisor's Plan:**
```
1. Route to Parser Agent: Parse document
2. Route to Analysis Agent: Summarize text
3. Route to Export Agent: Export tables as CSV
4. Aggregate and return all results
```

**Execution:**
```
Supervisor → Parser Agent
  ├─ Parses document
  ├─ Waits for completion
  └─ Returns job_id to Supervisor

Supervisor → Analysis Agent (with job_id)
  ├─ Gets text results
  ├─ Generates summary using LLM
  └─ Returns summary to Supervisor

Supervisor → Export Agent (with job_id)
  ├─ Gets tables
  ├─ Converts to CSV format
  └─ Returns CSV files to Supervisor

Supervisor → User
  └─ Presents: Summary + CSV files
```

---

## Use Cases and Examples

### Use Case 1: Batch Processing

**User:**
```
"Parse all PDFs in /documents/ folder with Gemini descriptions"
```

**Agent Flow:**
```
1. List files in folder
2. For each PDF:
   - Upload/reference file
   - Call parse_document with Gemini
   - Store job_id
3. Monitor all jobs concurrently
4. Return summary when all complete
```

---

### Use Case 2: Conditional Processing

**User:**
```
"Parse this document. If it has more than 5 tables, use high_quality mode
and give me detailed table analysis. Otherwise, just use fast mode."
```

**Agent Flow:**
```
1. Parse with fast mode first (quick preview)
2. Count tables in results
3. If count > 5:
   - Re-parse with high_quality mode
   - Extract all tables
   - Perform detailed analysis
4. Else:
   - Return fast mode results
```

---

### Use Case 3: Interactive Refinement

**Conversation:**
```
User: "Parse this annual report"
Agent: [Parses document] "Done! Found 50 pages, 12 tables, 25 images."

User: "Show me the financial tables"
Agent: [Filters tables] "Here are the 3 financial tables from pages 5, 12, and 18."

User: "Export those as CSV"
Agent: [Exports filtered tables] "Here are your CSV files: [links]"

User: "Now describe all the chart images with Gemini"
Agent: [Checks if descriptions already exist]
      "Those images weren't described during parsing. Let me process them now..."
      [Calls image description service]
      "Done! Here are the descriptions..."
```

---

### Use Case 4: Comparative Analysis

**User:**
```
"Parse report_2023.pdf and report_2024.pdf, then compare the financial tables"
```

**Agent Flow:**
```
1. Parse both documents in parallel
   - Job 1: report_2023.pdf
   - Job 2: report_2024.pdf

2. Monitor both jobs concurrently

3. When both complete:
   - Extract financial tables from both
   - Identify matching tables (by title/structure)
   - Perform comparison analysis
   - Generate summary of changes

4. Return comparative report
```

---

### Use Case 5: Smart Defaults

**Conversation:**
```
User: "Parse this document"
Agent: [Checks document] "This appears to be a scanned document. I'll use OCR mode. Proceed?"

User: "Yes"
Agent: [Parses with OCR] "Done! The OCR extracted text from 25 pages."

User: "Parse another one"
Agent: [Remembers preference] "Using OCR mode again. Starting..."
```

---

## Benefits Summary

### For Users

✅ **Natural Language Interface** - No need to learn API endpoints or parameters
✅ **Stateful Conversations** - Reference previous results naturally
✅ **Automatic Workflows** - Agent handles async operations and polling
✅ **Intelligent Defaults** - Agent suggests best options based on content
✅ **Error Recovery** - Agent retries and recovers from failures

### For Developers

✅ **Zero API Rewrite** - FastAPI-MCP wraps existing endpoints
✅ **Rapid Prototyping** - Build agentic features in hours, not weeks
✅ **Production Ready** - LangGraph handles persistence, recovery, scaling
✅ **Observable** - Graph visualization shows agent's decision path
✅ **Extensible** - Add new tools by adding new endpoints

### For Business

✅ **Reduced Training Costs** - Users interact naturally, no API docs needed
✅ **Higher Adoption** - Natural language lowers barrier to entry
✅ **Automation Opportunities** - Agents can handle complex workflows autonomously
✅ **Competitive Advantage** - AI-powered experience vs traditional APIs

---

## Getting Started

### Step 1: Install Dependencies

```bash
pip install fastapi-mcp langgraph langchain-core
```

### Step 2: Expose Your API as MCP Tools

```python
from fastapi import FastAPI
from fastapi_mcp import FastAPIMCP

app = FastAPI()
# ... your existing endpoints ...

# Expose as MCP server
mcp = FastAPIMCP(app)
mcp.run()
```

### Step 3: Build LangGraph Agent

```python
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Define state
class AgentState(TypedDict):
    messages: list
    job_id: str | None

# Define nodes
def parse_node(state): ...
def monitor_node(state): ...
def results_node(state): ...

# Build graph
graph = StateGraph(AgentState)
graph.add_node("parse", parse_node)
graph.add_node("monitor", monitor_node)
graph.add_node("results", results_node)

graph.set_entry_point("parse")
graph.add_edge("parse", "monitor")
graph.add_edge("monitor", "results")
graph.add_edge("results", END)

agent = graph.compile()
```

### Step 4: Run Agent

```python
result = agent.invoke({
    "messages": ["Parse /uploads/document.pdf with Gemini descriptions"]
})
```

---

## References and Resources

### FastAPI-MCP
- **GitHub**: https://github.com/tadata-org/fastapi_mcp
- **Tutorial**: https://medium.com/@manojjahgirdar/expose-fastapi-endpoints-securely-as-model-context-protocol-mcp-tools
- **Documentation**: Auto-generated from your FastAPI OpenAPI schema

### LangGraph
- **Official Site**: https://www.langchain.com/langgraph
- **GitHub**: https://github.com/langchain-ai/langgraph
- **Docs**: https://langchain-ai.github.io/langgraph/
- **Tutorial**: https://blog.langchain.com/building-langgraph/

### Model Context Protocol (MCP)
- **Specification**: https://modelcontextprotocol.io/
- **Anthropic MCP**: https://www.anthropic.com/news/model-context-protocol

### Related
- **LangChain**: https://python.langchain.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/

---

## Next Steps

1. **Experiment with FastAPI-MCP**: Expose your existing API as MCP tools
2. **Build Simple Agent**: Create a basic LangGraph agent with 2-3 tools
3. **Add State Management**: Implement persistent state for job tracking
4. **Test Workflows**: Try complex multi-step scenarios
5. **Add Human-in-the-Loop**: Implement approval nodes for expensive operations
6. **Scale to Multi-Agent**: Split into specialized agents as needed

---

## Conclusion

The combination of **FastAPI-MCP** and **LangGraph** transforms your document parser REST API into an intelligent, conversational, autonomous system that:

- Understands natural language requests
- Plans and executes complex workflows
- Manages state and memory across interactions
- Handles async operations automatically
- Recovers from errors gracefully
- Scales from simple queries to multi-agent orchestration

This architecture represents the future of API interaction - moving from rigid REST endpoints to flexible, intelligent agents that understand user intent and autonomously achieve goals.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Author**: Docling Parser Team
