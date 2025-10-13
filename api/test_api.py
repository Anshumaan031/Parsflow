"""
Simple test script to verify API is working
"""
import requests
import time
import sys


def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"

    print("=" * 80)
    print("Testing Docling Parser API")
    print("=" * 80)

    # 1. Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the API is running: python main.py")
        return

    # 2. Get API info
    print("\n2. Testing API info endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/info")
        info = response.json()
        print(f"   API Version: {info['api_version']}")
        print(f"   Supported formats: {len(info['supported_mime_types'])}")
        print(f"   Parsing modes: {info['parsing_modes']}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Upload a document (if you have one)
    print("\n3. Testing document upload...")
    print("   Note: Make sure you have 'picture_classification.pdf' in the project root")

    try:
        # Check if test file exists
        import os
        test_file = "../picture_classification.pdf"
        if not os.path.exists(test_file):
            print(f"   Skipping: Test file not found at {test_file}")
            print("   To test upload, place a PDF file and update the path above")
            return

        # Upload file
        with open(test_file, "rb") as f:
            files = {"file": f}
            data = {
                "parsing_mode": "standard",
                "extract_images": True,
                "extract_tables": True
            }
            response = requests.post(
                f"{base_url}/api/v1/parse/document",
                files=files,
                data=data
            )

        if response.status_code != 202:
            print(f"   Upload failed: {response.status_code}")
            print(f"   Response: {response.json()}")
            return

        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"   ✓ Upload successful!")
        print(f"   Job ID: {job_id}")

        # 4. Check job status
        print("\n4. Checking job status...")
        max_attempts = 30
        for i in range(max_attempts):
            response = requests.get(f"{base_url}/api/v1/parse/jobs/{job_id}")
            status_data = response.json()
            status = status_data["status"]
            progress = status_data.get("progress_percent", 0)

            print(f"   Status: {status} ({progress}%)")

            if status == "completed":
                print("   ✓ Parsing completed!")
                break
            elif status == "failed":
                print(f"   ✗ Parsing failed: {status_data.get('error_message')}")
                return

            time.sleep(2)
        else:
            print("   ⚠ Timeout waiting for results")
            return

        # 5. Get results
        print("\n5. Fetching results...")
        response = requests.get(f"{base_url}/api/v1/parse/results/{job_id}")
        results = response.json()

        print(f"   ✓ Results retrieved!")
        print(f"   Filename: {results['metadata']['filename']}")
        print(f"   Pages: {results['metadata']['page_count']}")
        print(f"   Text items: {results['statistics']['total_text_items']}")
        print(f"   Tables: {results['statistics']['total_tables']}")
        print(f"   Pictures: {results['statistics']['total_pictures']}")

        # 6. Get texts
        print("\n6. Testing filtered endpoints...")
        response = requests.get(f"{base_url}/api/v1/parse/results/{job_id}/texts")
        texts_data = response.json()
        print(f"   ✓ Texts endpoint: {texts_data['count']} items")

        # 7. Get tables
        response = requests.get(f"{base_url}/api/v1/parse/results/{job_id}/tables")
        tables_data = response.json()
        print(f"   ✓ Tables endpoint: {tables_data['count']} items")

        # 8. Export markdown
        print("\n7. Testing export endpoints...")
        response = requests.get(f"{base_url}/api/v1/parse/results/{job_id}/export/markdown")
        markdown_content = response.text
        print(f"   ✓ Markdown export: {len(markdown_content)} characters")

        print("\n" + "=" * 80)
        print("All tests completed successfully! ✓")
        print("=" * 80)

    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_api()
