"""
Quick Start Example
Simplest way to get started with RAG on your documents
"""
import os
from pathlib import Path

# Check dependencies
try:
    import requests
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    print("✅ All dependencies installed")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nPlease install requirements:")
    print("  pip install -r requirements.txt")
    exit(1)

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not set")
    print("\nPlease set your OpenAI API key:")
    print("  Windows: set OPENAI_API_KEY=your-key-here")
    print("  Linux/Mac: export OPENAI_API_KEY=your-key-here")
    exit(1)

print("✅ OpenAI API key found")

# Check if API is running
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("✅ Docling API is running")
    else:
        print("⚠️  API returned unexpected status")
except Exception as e:
    print("❌ Cannot connect to Docling API")
    print("\nPlease start the API first:")
    print("  cd ..")
    print("  python main.py")
    exit(1)

print("\n" + "="*60)
print("🚀 QUICK START - RAG WITH DOCLING")
print("="*60)

print("\n📚 Available Examples:\n")
print("1. Simple Text-Only RAG")
print("   python simple_rag.py <document.pdf> \"Your question\"")
print("   Example: python simple_rag.py report.pdf \"What is the main topic?\"")

print("\n2. Multimodal RAG with Images")
print("   python multimodal_rag.py <document.pdf> \"Your question\"")
print("   Example: python multimodal_rag.py report.pdf \"Explain the chart\"")

print("\n3. Image Enrichment (standalone)")
print("   python image_enrichment.py <document.pdf>")
print("   Example: python image_enrichment.py report.pdf")

print("\n" + "="*60)
print("\n💡 Tips:")
print("- Use simple_rag.py for text-only documents (faster, cheaper)")
print("- Use multimodal_rag.py when you need to analyze charts/images")
print("- Both scripts support interactive mode after the first query")
print("- Image enrichment takes 2-3 seconds per image")
print("- Results are cached in the vector store for faster retrieval")

print("\n📖 For more details, see README.md")
print("\n✅ Setup complete! You're ready to go!")
