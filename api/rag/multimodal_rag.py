"""
Multimodal RAG Pipeline with Images
Demonstrates advanced RAG with image understanding using vision models
"""
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS


# Configuration
API_BASE_URL = "http://localhost:8000"
PARSING_MODE = "high_quality"  # Better for image extraction
IMAGE_SCALE = 3.0  # Higher quality for vision models


def upload_document(file_path: str) -> str:
    """Upload document with high-quality image extraction"""
    print(f"📤 Uploading document: {Path(file_path).name}")

    url = f"{API_BASE_URL}/api/v1/parse/document"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {
            'parsing_mode': PARSING_MODE,
            'extract_images': True,
            'extract_tables': True,
            'images_scale': IMAGE_SCALE
        }

        response = requests.post(url, files=files, params=params)
        response.raise_for_status()

    result = response.json()
    print(f"✅ Document uploaded. Job ID: {result['job_id']}")
    return result['job_id']


def wait_for_completion(job_id: str, poll_interval: int = 2) -> Dict[str, Any]:
    """Poll job status until completion"""
    status_url = f"{API_BASE_URL}/api/v1/parse/jobs/{job_id}"

    print("⏳ Waiting for document processing...")

    while True:
        response = requests.get(status_url)
        response.raise_for_status()
        status = response.json()

        print(f"   Status: {status['status']} - Progress: {status.get('progress_percent', 0)}%")

        if status['status'] == 'completed':
            print("✅ Processing completed!")
            break
        elif status['status'] == 'failed':
            raise Exception(f"Processing failed: {status.get('error_message')}")

        time.sleep(poll_interval)

    results_url = f"{API_BASE_URL}/api/v1/parse/results/{job_id}"
    response = requests.get(results_url)
    response.raise_for_status()

    return response.json()


def enrich_image_with_vision(image_data: Dict[str, Any], llm_vision: ChatOpenAI) -> str:
    """
    Generate detailed description of image using GPT-4 Vision

    Args:
        image_data: Image metadata with base64 URI
        llm_vision: Vision-capable LLM

    Returns:
        Detailed image description
    """
    caption = image_data.get('caption', '')
    image_uri = image_data.get('image_uri')

    if not image_uri:
        return caption or "Image without data"

    # Create vision prompt
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Analyze this image from a document and provide a detailed description for a search system.

Include:
1. Type of visual (chart, diagram, photo, table, etc.)
2. Main content and purpose
3. Any text visible in the image
4. Key data points, trends, or insights
5. Colors, labels, and visual elements

Be specific and detailed to help with document search and question answering."""
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_uri}
                }
            ]
        }
    ]

    try:
        response = llm_vision.invoke(messages)
        description = response.content

        # Combine caption and description
        if caption:
            return f"Caption: {caption}\n\nDetailed Description: {description}"
        return description

    except Exception as e:
        print(f"   ⚠️  Warning: Failed to process image: {str(e)}")
        return caption or "Image processing failed"


def create_multimodal_documents(parse_result: Dict[str, Any]) -> List[Document]:
    """
    Create documents with enriched image descriptions

    Args:
        parse_result: API response with parsed content

    Returns:
        List of Document objects
    """
    print("📄 Creating multimodal document chunks...")

    documents = []
    llm_vision = ChatOpenAI(model="gpt-4o", temperature=0)

    # Add text items
    print("   Processing text items...")
    for text_item in parse_result['content']['texts']:
        doc = Document(
            page_content=text_item['text'],
            metadata={
                'type': 'text',
                'label': text_item['label'],
                'page': text_item.get('page'),
                'source': parse_result['metadata']['filename']
            }
        )
        documents.append(doc)

    # Add tables
    print("   Processing tables...")
    for table in parse_result['content']['tables']:
        table_text = f"Table on page {table.get('page', 'unknown')}"
        if table.get('dataframe_csv'):
            table_text += f":\n{table['dataframe_csv']}"

        doc = Document(
            page_content=table_text,
            metadata={
                'type': 'table',
                'page': table.get('page'),
                'table_id': table['id'],
                'source': parse_result['metadata']['filename']
            }
        )
        documents.append(doc)

    # Add enriched images
    images = parse_result['content']['pictures']
    if images:
        print(f"   Processing {len(images)} images with vision model...")

        for i, image in enumerate(images, 1):
            print(f"      Image {i}/{len(images)}...", end=" ")

            # Generate detailed description
            description = enrich_image_with_vision(image, llm_vision)

            doc = Document(
                page_content=description,
                metadata={
                    'type': 'image',
                    'page': image.get('page'),
                    'image_id': image['id'],
                    'image_uri': image.get('image_uri'),  # Store for later retrieval
                    'source': parse_result['metadata']['filename']
                }
            )
            documents.append(doc)
            print("✓")

    print(f"✅ Created {len(documents)} multimodal chunks")
    return documents


def build_vector_store(documents: List[Document]) -> FAISS:
    """Build FAISS vector store from multimodal documents"""
    print("🔧 Building vector store...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    split_docs = text_splitter.split_documents(documents)
    print(f"   Split into {len(split_docs)} chunks")

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    print("✅ Vector store created")
    return vectorstore


def query_multimodal(vectorstore: FAISS, query: str, k: int = 4) -> str:
    """
    Query documents with multimodal context

    Args:
        vectorstore: FAISS vector store
        query: User question
        k: Number of results to retrieve

    Returns:
        Answer string
    """
    print(f"\n❓ Query: {query}")
    print("🔍 Searching documents...")

    # Retrieve relevant documents
    docs = vectorstore.similarity_search(query, k=k)

    # Separate text and image contexts
    text_contexts = []
    image_contexts = []

    print("\n📚 Retrieved Context:")
    for i, doc in enumerate(docs, 1):
        doc_type = doc.metadata.get('type', 'unknown')
        page = doc.metadata.get('page', '?')

        if doc_type == 'image':
            print(f"{i}. [IMAGE] Page {page}")
            print(f"   {doc.page_content[:150]}...")
            image_contexts.append(doc)
        else:
            print(f"{i}. [{doc.metadata.get('label', doc_type).upper()}] Page {page}")
            print(f"   {doc.page_content[:150]}...")
            text_contexts.append(doc)

    # Build multimodal prompt
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant analyzing documents. Answer questions based on the provided text and image descriptions. Be specific and reference the sources."
        },
        {
            "role": "user",
            "content": []
        }
    ]

    # Add text context
    text_content = f"Question: {query}\n\nContext:\n\n"
    for i, doc in enumerate(text_contexts, 1):
        text_content += f"{i}. [{doc.metadata.get('label', 'text')}] Page {doc.metadata.get('page')}:\n{doc.page_content}\n\n"

    messages[1]["content"].append({
        "type": "text",
        "text": text_content
    })

    # Add image context (with actual images if available)
    for i, doc in enumerate(image_contexts, 1):
        # Add image description
        messages[1]["content"].append({
            "type": "text",
            "text": f"\nImage {i} Description (Page {doc.metadata.get('page')}):\n{doc.page_content}\n"
        })

        # Add actual image for vision model to see
        if doc.metadata.get('image_uri'):
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": doc.metadata['image_uri']}
            })

    # Generate answer with vision model
    print("\n🤖 Generating answer with vision model...")
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response = llm.invoke(messages)

    print(f"\n💡 Answer:\n{response.content}")
    return response.content


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python multimodal_rag.py <document_path> [query]")
        print("Example: python multimodal_rag.py report.pdf 'What does the revenue chart show?'")
        sys.exit(1)

    file_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "Summarize this document including any charts or diagrams."

    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    try:
        # 1. Upload and parse document
        job_id = upload_document(file_path)

        # 2. Wait for completion
        result = wait_for_completion(job_id)

        # 3. Display statistics
        stats = result['statistics']
        print(f"\n📊 Document Statistics:")
        print(f"   Pages: {result['metadata']['page_count']}")
        print(f"   Text items: {stats['total_text_items']}")
        print(f"   Tables: {stats['total_tables']}")
        print(f"   Images: {stats['total_pictures']}")

        # 4. Create multimodal documents with vision enrichment
        documents = create_multimodal_documents(result)

        # 5. Build vector store
        vectorstore = build_vector_store(documents)

        # 6. Query with multimodal context
        answer = query_multimodal(vectorstore, query)

        # Interactive mode
        print("\n" + "="*60)
        print("💬 Interactive Multimodal Mode (type 'quit' to exit)")
        print("="*60)

        while True:
            user_query = input("\n❓ Your question: ").strip()
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            if not user_query:
                continue

            query_multimodal(vectorstore, user_query)

        print("\n👋 Goodbye!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
