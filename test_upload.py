"""
Test script for PDF upload API
Usage: python test_upload.py <pdf_file_path>
"""
import requests
import sys
import os

def upload_pdf(file_path: str):
    """Test PDF upload endpoint"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    if not file_path.lower().endswith('.pdf'):
        print(f"❌ File must be a PDF: {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"📤 Uploading: {file_name}")
    print(f"   Size: {file_size / 1024:.2f} KB\n")
    
    url = "http://localhost:8000/api/v1/upload"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful!\n")
            print(f"📄 Document ID: {data['document_id']}")
            print(f"📖 Filename: {data['filename']}")
            print(f"📑 Pages: {data['page_count']}")
            print(f"📝 Text length: {data['text_length']:,} characters")
            print(f"🔢 Chunks created: {data['chunks_count']}")
            print(f"\n💡 Use this document ID for character extraction:")
            print(f"   python test_characters.py {data['document_id']}")
        else:
            print(f"❌ Upload failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Is the server running on http://localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_upload.py <pdf_file_path>")
        print("\nExample:")
        print('  python test_upload.py "C:\\Users\\ASUS\\Downloads\\pinocchio.pdf"')
        sys.exit(1)
    
    file_path = sys.argv[1]
    upload_pdf(file_path)
