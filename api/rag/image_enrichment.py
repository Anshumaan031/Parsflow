"""
Image Enrichment Utility
Standalone script for generating detailed image descriptions from parsed documents
"""
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI


# Configuration
API_BASE_URL = "http://localhost:8000"


def upload_and_parse(file_path: str) -> Dict[str, Any]:
    """Upload document and wait for parsing"""
    print(f"📤 Uploading: {Path(file_path).name}")

    # Upload
    url = f"{API_BASE_URL}/api/v1/parse/document"
    with open(file_path, 'rb') as f:
        response = requests.post(
            url,
            files={'file': f},
            params={
                'parsing_mode': 'high_quality',
                'extract_images': True,
                'images_scale': 3.0
            }
        )
        response.raise_for_status()

    job_id = response.json()['job_id']
    print(f"Job ID: {job_id}")

    # Wait for completion
    status_url = f"{API_BASE_URL}/api/v1/parse/jobs/{job_id}"
    while True:
        status = requests.get(status_url).json()
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            raise Exception(f"Parsing failed: {status.get('error_message')}")
        time.sleep(2)

    # Get results
    results_url = f"{API_BASE_URL}/api/v1/parse/results/{job_id}"
    return requests.get(results_url).json()


def enrich_image(image: Dict[str, Any], index: int, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Generate rich description for a single image

    Args:
        image: Image data from API
        index: Image number
        llm: Vision model

    Returns:
        Enriched image data
    """
    print(f"\n🖼️  Image {index}")
    print(f"   Page: {image.get('page', '?')}")
    print(f"   Original Caption: {image.get('caption', 'None')}")

    if not image.get('image_uri'):
        print("   ⚠️  No image data available")
        return {
            **image,
            'enriched_description': image.get('caption', 'No description available')
        }

    # Generate description
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Analyze this image from a document and provide a comprehensive description.

Please include:

1. **Type**: What kind of visual is this? (chart, graph, diagram, photo, screenshot, table, illustration, etc.)

2. **Content**: What is shown in the image?
   - Main subject or topic
   - Key elements and components
   - Purpose or message

3. **Text**: Any text visible in the image
   - Titles, labels, legends
   - Data values, annotations
   - Captions or notes

4. **Data & Insights**: For charts/graphs
   - What data is displayed?
   - Trends, patterns, comparisons
   - Key findings or takeaways

5. **Visual Details**:
   - Colors used
   - Layout and structure
   - Important visual elements

Be detailed and specific to help with document search and understanding."""
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image['image_uri']}
                }
            ]
        }
    ]

    try:
        response = llm.invoke(messages)
        description = response.content

        print(f"   ✅ Generated description ({len(description)} chars)")
        print(f"\n   Description Preview:")
        print(f"   {description[:200]}...")

        return {
            **image,
            'enriched_description': description,
            'has_enrichment': True
        }

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {
            **image,
            'enriched_description': image.get('caption', 'Processing failed'),
            'has_enrichment': False,
            'error': str(e)
        }


def process_all_images(parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process all images in document"""
    images = parse_result['content']['pictures']

    if not images:
        print("ℹ️  No images found in document")
        return []

    print(f"\n🔍 Processing {len(images)} images...")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    enriched_images = []

    for i, image in enumerate(images, 1):
        enriched = enrich_image(image, i, llm)
        enriched_images.append(enriched)

    return enriched_images


def save_results(enriched_images: List[Dict[str, Any]], output_file: str):
    """Save enriched image data to JSON file"""
    output_path = Path(output_file)

    # Prepare output (remove base64 URIs for readability)
    output_data = []
    for img in enriched_images:
        output_data.append({
            'id': img['id'],
            'page': img.get('page'),
            'original_caption': img.get('caption'),
            'enriched_description': img.get('enriched_description'),
            'has_enrichment': img.get('has_enrichment', False),
            'bbox': img.get('bbox'),
            'has_image_data': bool(img.get('image_uri'))
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved results to: {output_path}")


def display_summary(enriched_images: List[Dict[str, Any]]):
    """Display summary of enrichment"""
    total = len(enriched_images)
    enriched = sum(1 for img in enriched_images if img.get('has_enrichment'))

    print("\n" + "="*60)
    print("📊 ENRICHMENT SUMMARY")
    print("="*60)
    print(f"Total images: {total}")
    print(f"Successfully enriched: {enriched}")
    print(f"Failed: {total - enriched}")

    print("\n📝 Image Details:")
    for i, img in enumerate(enriched_images, 1):
        status = "✅" if img.get('has_enrichment') else "❌"
        desc_len = len(img.get('enriched_description', ''))
        print(f"{status} Image {i} (Page {img.get('page', '?')}): {desc_len} chars")


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python image_enrichment.py <document_path> [output_file]")
        print("\nExample:")
        print("  python image_enrichment.py report.pdf")
        print("  python image_enrichment.py report.pdf enriched_images.json")
        sys.exit(1)

    file_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "enriched_images.json"

    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    try:
        # Parse document
        result = upload_and_parse(file_path)

        # Display document info
        print("\n📄 Document Information:")
        print(f"   Filename: {result['metadata']['filename']}")
        print(f"   Pages: {result['metadata']['page_count']}")
        print(f"   Images: {result['statistics']['total_pictures']}")

        # Process images
        enriched_images = process_all_images(result)

        if enriched_images:
            # Display summary
            display_summary(enriched_images)

            # Save results
            save_results(enriched_images, output_file)

            print("\n✅ Image enrichment complete!")
        else:
            print("\nℹ️  No images to process")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
