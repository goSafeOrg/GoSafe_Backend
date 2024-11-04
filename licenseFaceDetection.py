import cv2

def extract_face_from_license(license_image_path, output_path="extracted_face.jpg", padding=60):
    """
    Detects and extracts the face from the license image, with optional padding for clarity.

    Parameters:
    license_image_path (str): Path to the license image.
    output_path (str): Path where the extracted face image will be saved.
    padding (int): Amount of padding to add around the face region.

    Returns:
    str: Path to the saved face image, or None if detection fails.
    """
    # Load the license image
    image = cv2.imread(license_image_path)
    if image is None:
        print("Could not read the license image.")
        return None

    # Convert to grayscale for better face detection accuracy
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Load the Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error loading Haar cascade.")
        return None

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No face detected in the license image.")
        return None

    # Assume the largest detected face is the target face (useful if multiple faces are detected)
    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])

    # Apply padding, ensuring the padding stays within image bounds
    x1 = max(x - padding, 0)
    y1 = max(y - padding, 0)
    x2 = min(x + w + padding, image.shape[1])
    y2 = min(y + h + padding, image.shape[0])

    # Crop the face region with padding from the license image
    face_region = image[y1:y2, x1:x2]

    # Save the extracted face image
    cv2.imwrite(output_path, face_region)
    print(f"Extracted face image with padding saved to {output_path}")
    
    return output_path

face_image_path = extract_face_from_license("hlf.jpeg")
if face_image_path:
    print("Face extracted successfully:", face_image_path)