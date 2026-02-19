"""
Ayahay SmartScan - OCR Engine (The Brain)
Processes images to extract and validate container IDs using OpenCV and PyTesseract.
"""

import cv2
import pytesseract
import re
import platform
from pathlib import Path
from typing import Optional, Dict, List
from stdnum import iso6346

# Windows-specific Tesseract path configuration
if platform.system() == 'Windows':
    # Common Tesseract installation paths on Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            break


def preprocess_image(image_path: Path) -> cv2.Mat:
    """
    Preprocess image for better OCR accuracy.
    Converts to grayscale and applies thresholding.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Preprocessed OpenCV image matrix
    """
    # Read image
    img = cv2.imread(str(image_path))
    
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to get binary image
    # THRESH_BINARY + OTSU for automatic threshold calculation
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh


def extract_text(image_path: Path) -> str:
    """
    Extract text from image using PyTesseract OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text string
    """
    # Preprocess image
    processed_img = preprocess_image(image_path)
    
    # Configure Tesseract for better container ID recognition
    # Use PSM 6 (assume uniform block of text) and whitelist alphanumeric
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    # Run OCR
    text = pytesseract.image_to_string(processed_img, config=custom_config)
    
    return text


def find_container_ids(text: str) -> List[str]:
    """
    Extract container IDs from text using regex pattern.
    Container ID format: 4 uppercase letters + 7 digits (e.g., ABCD1234567)
    
    Args:
        text: Text string to search
        
    Returns:
        List of found container ID strings
    """
    # Pattern: 4 uppercase letters followed by 7 digits
    pattern = r'[A-Z]{4}\d{7}'
    
    # Find all matches
    matches = re.findall(pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
    
    return unique_matches


def validate_container_id(container_id: str) -> Dict[str, any]:
    """
    Validate container ID using ISO 6346 check-digit algorithm.
    
    Args:
        container_id: Container ID string (format: ABCD1234567)
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'container_id': str,
            'check_digit': str or None,
            'error': str or None
        }
    """
    result = {
        'valid': False,
        'container_id': container_id,
        'check_digit': None,
        'error': None
    }
    
    try:
        # ISO 6346 validation includes check-digit verification
        # The last digit is the check digit
        if len(container_id) == 11:
            # Extract owner code (first 3 letters), equipment code (4th letter), 
            # serial number (6 digits), and check digit (last digit)
            owner_code = container_id[:3]
            equipment_code = container_id[3]
            serial_number = container_id[4:10]
            check_digit = container_id[10]
            
            # Validate using python-stdnum
            # iso6346.validate() checks the check digit
            iso6346.validate(container_id)
            
            result['valid'] = True
            result['check_digit'] = check_digit
            
        else:
            result['error'] = f"Invalid length: expected 11 characters, got {len(container_id)}"
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


def process_image(image_path: Path) -> Dict[str, any]:
    """
    Main function to process an image and extract/validate container IDs.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with processing results:
        {
            'success': bool,
            'raw_text': str,
            'container_ids_found': List[str],
            'validated_ids': List[Dict],
            'best_match': Dict or None,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'raw_text': '',
        'container_ids_found': [],
        'validated_ids': [],
        'best_match': None,
        'error': None
    }
    
    try:
        # Extract text from image
        raw_text = extract_text(image_path)
        result['raw_text'] = raw_text
        
        # Find container IDs
        container_ids = find_container_ids(raw_text)
        result['container_ids_found'] = container_ids
        
        if not container_ids:
            result['error'] = "No container IDs found in image"
            return result
        
        # Validate each found container ID
        validated = []
        for cid in container_ids:
            validation = validate_container_id(cid)
            validated.append(validation)
            
            # Track the first valid one as best match
            if validation['valid'] and result['best_match'] is None:
                result['best_match'] = validation
        
        result['validated_ids'] = validated
        result['success'] = True
        
        # If no valid IDs found, set error
        if result['best_match'] is None:
            result['error'] = "Found container IDs but none passed ISO 6346 validation"
            result['success'] = False
        
    except Exception as e:
        result['error'] = str(e)
    
    return result
