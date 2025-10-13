"""
Simple Text-Only RAG Pipeline
Demonstrates basic document parsing and question answering without images
"""
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA


# Configuration
API_BASE_URL = "http://localhost:8000"
PARSING_MODE = "standard"


def upload_document(file_path: str) -> str:
    """
    Upload document to Docling Parser API

    Args:
        file_path: Path to document file

    Returns:
        job_id for tracking
    """
    print(f"📤 Uploading document: {Path(file_path).name}")

    url = f"{API_BASE_URL}/api/v1/parse/document"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {
            'parsing_mode': PARSING_MODE,
            'extract_images': False,  # Text-only for simple RAG
            'extract_tables': True
        }

        response = requests.post(url, files=files, params=params)
        response.raise_for_status()

    result = response.json()
    print(f"✅ Document uploaded. Job ID: {result['job_id']}")
    return result['job_id']


def wait_for_completion(job_id: str, poll_interval: int = 2) -> Dict[str, Any]:
    """
    Poll job status until completion

    Args:
        job_id: Job identifier
        poll_interval: Seconds between polls

    Returns:
        Complete parsing result
    """
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

    # Get full results
    results_url = f"{API_BASE_URL}/api/v1/parse/results/{job_id}"
    response = requests.get(results_url)
    response.raise_for_status()

    return response.json()


def create_documents(parse_result: Dict[str, Any]) -> List[Document]:
    """
    Convert parse results to LangChain documents

    Args:
        parse_result: API response with parsed content

    Returns:
        List of Document objects
    """
    print("📄 Creating document chunks...")

    documents = []

    # Add text items
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

    # Add table data as text
    for table in parse_result['content']['tables']:
        # Convert table to text description
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

    print(f"✅ Created {len(documents)} document chunks")
    return documents


def build_vector_store(documents: List[Document]) -> FAISS:
    """
    Build FAISS vector store from documents

    Args:
        documents: List of Document objects

    Returns:
        FAISS vector store
    """
    print("🔧 Building vector store...")

    # Split large documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    split_docs = text_splitter.split_documents(documents)
    print(f"   Split into {len(split_docs)} chunks")

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)

    print("✅ Vector store created")
    return vectorstore


def query_documents(vectorstore: FAISS, query: str) -> str:
    """
    Query documents using RAG

    Args:
        vectorstore: FAISS vector store
        query: User question

    Returns:
        Answer string
    """
    print(f"\n❓ Query: {query}")
    print("🔍 Searching documents...")

    # Create QA chain
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    # Query
    result = qa_chain.invoke({"query": query})

    # Display sources
    print("\n📚 Retrieved Context:")
    for i, doc in enumerate(result['source_documents'], 1):
        print(f"{i}. [{doc.metadata['label']}] Page {doc.metadata.get('page', '?')}")
        print(f"   {doc.page_content[:150]}...")

    print(f"\n💡 Answer:\n{result['result']}")
    return result['result']


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python simple_rag.py <document_path> [query]")
        print("Example: python simple_rag.py sample.pdf 'What is this document about?'")
        sys.exit(1)

    file_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "What is this document about?"

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

        # 4. Create documents
        documents = create_documents(result)

        # 5. Build vector store
        vectorstore = build_vector_store(documents)

        # 6. Query
        answer = query_documents(vectorstore, query)

        # Interactive mode
        print("\n" + "="*60)
        print("💬 Interactive Mode (type 'quit' to exit)")
        print("="*60)

        while True:
            user_query = input("\n❓ Your question: ").strip()
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            if not user_query:
                continue

            query_documents(vectorstore, user_query)

        print("\n👋 Goodbye!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
