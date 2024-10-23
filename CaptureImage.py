import cv2
import requests

def capture_image():
    # Capture image from webcam
    cap = cv2.VideoCapture(0)
    success, img = cap.read()

    if success:
        # Save the captured image locally
        cv2.imwrite("captured_image.jpg", img)
    else:
        print("Failed to capture image")
    
    cap.release()

def send_image_to_api(image_path):
    url = 'http://127.0.0.1:5000/compare_faces'
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post(url, files=files)

    return response.json()

if __name__ == "__main__":
    capture_image()
    result = send_image_to_api('captured_image.jpg')
    print(f"Match: {result['match']}, Name: {result['name']}")
