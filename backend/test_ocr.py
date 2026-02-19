"""
Test script for OCR Engine Module 3
Run this to test OCR functionality before integrating with the full server.
"""

from pathlib import Path
from ocr_engine import process_image
import sys


def test_ocr(image_path: str):
    """
    Test OCR engine with a sample image.
    
    Usage:
        python test_ocr.py path/to/image.jpg
    """
    image_file = Path(image_path)
    
    if not image_file.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        return
    
    print(f"📸 Processing image: {image_path}")
    print("-" * 60)
    
    try:
        # Process image
        result = process_image(image_file)
        
        # Display results
        print(f"\n✅ OCR Processing Complete")
        print(f"Success: {result['success']}")
        
        if result.get('raw_text'):
            print(f"\n📝 Extracted Text (first 500 chars):")
            print("-" * 60)
            print(result['raw_text'][:500])
            print("-" * 60)
        
        if result.get('container_ids_found'):
            print(f"\n🔍 Container IDs Found: {len(result['container_ids_found'])}")
            for cid in result['container_ids_found']:
                print(f"  - {cid}")
        else:
            print("\n⚠️  No container IDs found in image")
        
        if result.get('validated_ids'):
            print(f"\n✅ Validation Results:")
            for validation in result['validated_ids']:
                status = "✓ VALID" if validation['valid'] else "✗ INVALID"
                print(f"  {status}: {validation['container_id']}")
                if validation.get('error'):
                    print(f"    Error: {validation['error']}")
        
        if result.get('best_match'):
            print(f"\n🎯 Best Match:")
            best = result['best_match']
            print(f"  Container ID: {best['container_id']}")
            print(f"  Valid: {best['valid']}")
            if best.get('check_digit'):
                print(f"  Check Digit: {best['check_digit']}")
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ocr.py <image_path>")
        print("\nExample:")
        print("  python test_ocr.py uploads/scan_20240219_123456.jpg")
        print("  python test_ocr.py test_image.jpg")
        sys.exit(1)
    
    test_ocr(sys.argv[1])
