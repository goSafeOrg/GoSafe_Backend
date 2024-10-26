from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import cv2
import os 
from ocr_processor import process_image, extract_key_value_pairs
app = Flask(__name__)


# Set directory for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# API route to handle file upload and OCR processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save the uploaded file to the uploads directory
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Process the image and extract text using OCR
        text = process_image(file_path)

        # Extract key-value pairs from the text
        key_value_pairs = extract_key_value_pairs(text)

        # Return the extracted information as JSON
        return jsonify({"data": key_value_pairs})
    
@app.route('/test', methods=['GET'])
def test():
   
        return jsonify({"data": "Route is working"})

@app.route('/compare_faces', methods=['POST'])
def compare_faces():
    # Get the two images from the POST request
    file1 = request.files['image1']
    file2 = request.files['image2']
    
    # Convert both images to numpy arrays
    img1_np = np.frombuffer(file1.read(), np.uint8)
    img2_np = np.frombuffer(file2.read(), np.uint8)
    
    # Decode images
    img1 = cv2.imdecode(img1_np, cv2.IMREAD_COLOR)
    img2 = cv2.imdecode(img2_np, cv2.IMREAD_COLOR)

    # Convert images to RGB (required by face_recognition library)
    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    # Detect face encodings in both images
    encodes1 = face_recognition.face_encodings(img1_rgb)
    encodes2 = face_recognition.face_encodings(img2_rgb)

    if len(encodes1) == 0 or len(encodes2) == 0:
        return jsonify({"match": False, "error": "No face detected in one or both images"})

    # We are only considering the first face in both images (if multiple faces are detected)
    encode1 = encodes1[0]
    encode2 = encodes2[0]

    # Compare faces
    matches = face_recognition.compare_faces([encode1], encode2)
    face_distance = face_recognition.face_distance([encode1], encode2)

    # Return the result of the comparison
    if matches[0]:
        return jsonify({"match": True, "distance": face_distance[0]})
    else:
        return jsonify({"match": False, "distance": face_distance[0]})

if __name__ == '__main__':
    app.run(debug=True)
