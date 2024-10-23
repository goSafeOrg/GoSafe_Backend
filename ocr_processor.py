import re
import cv2
import pytesseract

# Function to preprocess the image and extract text using Tesseract OCR
def process_image(image_path):
    # Load image and preprocess
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
    
    # Tesseract configuration
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    custom_config = r'--oem 3 --psm 11'

    # Run Tesseract OCR
    text = pytesseract.image_to_string(threshed, lang='eng')
    return text

# Function to extract key-value pairs from the OCR text
def extract_key_value_pairs(text):
    lines = text.split("\n")  # Split text into lines
    key_value_pairs = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            key_value_pairs[key] = value
        elif "of" in line.lower():  # Handle cases like "Date of Validity"
            match = re.match(r"(.*?of\s+\w+)\s+(.+)", line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                key_value_pairs[key] = value
        else:
            # Handle cases where no clear separator exists
            if "No." in line or "Date" in line or "Reference" in line or "Blood" in line:
                parts = line.split()
                if len(parts) > 1:
                    key = parts[0].strip() + " " + parts[1].strip()
                    value = " ".join(parts[2:]).strip()
                    key_value_pairs[key] = value
    
    return {"dob":key_value_pairs["Date of Birth"],"licnese_no":key_value_pairs["Reference No."]}
