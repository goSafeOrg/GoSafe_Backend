import cv2
import requests
import time
import pyttsx3
from datetime import datetime
import os
import json

engine = pyttsx3.init()

# Voice prompt to show license
def voice_prompt(message):
    engine.say(message)
    engine.runAndWait()

CACHE_DIR = 'cached_member_images'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def fetch_member_images():
    # Check if cached images exist
    cached_images = os.listdir(CACHE_DIR)
    if cached_images:
        # Return cached images if available
        return [os.path.join(CACHE_DIR, image) for image in cached_images]

    # Fetch images from Supabase if cache is empty
    member_image_urls = []
    try:
        response = requests.get('YOUR_SUPABASE_ENDPOINT/utils')
        if response.ok:
            member_data = response.json()
            member_image_urls = [member['image_url'] for member in member_data['data']]  # Adjust according to your data structure
            
            # Download and cache each member image
            for image_url in member_image_urls:
                image_response = requests.get(image_url)
                if image_response.ok:
                    image_name = os.path.basename(image_url)
                    image_path = os.path.join(CACHE_DIR, image_name)
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)
                else:
                    print(f"Failed to download image from {image_url}")

            return [os.path.join(CACHE_DIR, os.path.basename(url)) for url in member_image_urls]
        else:
            print("Failed to fetch member images from Supabase")
    except Exception as e:
        print(f"Error fetching member images: {e}")

    return []

# Capture and save an image from the webcam
def capture_image(image_name="captured_image.jpg"):
    cap = cv2.VideoCapture(0)
    success, img = cap.read()
    if success:
        cv2.imwrite(image_name, img)
    cap.release()
    return success, image_name

# Send license image to OCR API
def send_license_to_api(image_path):
    url = 'http://127.0.0.1:5000/upload'
    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        response = requests.post(url, files=files)
    return response.json()

# Authenticate license and retrieve license image
def authenticate_license(dob, license_id):
    url = f'http://public-api/license/validate?dob={dob}&license_id={license_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('image_url'), data.get('status')  # Image URL and status
    return None, None

# Send captured face to comparison API
def compare_face(image_path, license_image_url):
    url = 'http://127.0.0.1:5000/compare_faces'
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        data = {'license_image_url': license_image_url}
        response = requests.post(url, files=files, data=data)
    return response.json()

# Send notification to user
def send_notification(user_id, message, name, from_user, license_id, description, image_url, status="Pending"):
    # Step 1: Retrieve the Expo token for push notification
    expo_token = get_user_expo_token(user_id)
    
    # Step 2: Insert notification details into the notifications table
    notification_response = supabase.from_("notifications").insert({
        "name": name,
        "from_user": from_user,
        "license_id": license_id,
        "description": description,
        "image": image_url,
        "status": status,
        "message": message
    }).execute()

    # Check if notification was inserted successfully and retrieve its ID
    if notification_response.get("data"):
        notification_id = notification_response["data"][0]["id"]
        
        # Step 3: Update the utility table to add this notification ID under the user
        utility_response = supabase.from_("utility").update({
            "notifications": supabase.func.array_append("notifications", notification_id)
        }).eq("user_id", user_id).execute()

        # Step 4: Send the push notification to the user
        if expo_token:
            payload = {
                "to": expo_token,
                "title": "License Verification",
                "body": message
            }
            push_response = requests.post('https://exp.host/--/api/v2/push/send', json=payload)
            
            # Log event based on push notification status
            if push_response.status_code == 200:
                log_verification_event(user_id, "Notification Sent", message)
            else:
                print("Failed to send push notification:", push_response.text)
                
        # Log success of adding notification to utility table
        if utility_response.get("status_code") == 200:
            log_verification_event(user_id, "Notification Added to Utility", f"Notification ID {notification_id}")
        else:
            print("Failed to update utility table:", utility_response.get("error"))
            
    else:
        print("Failed to add notification:", notification_response.get("error"))


# Get user Expo token from database (Mock function)
def get_user_expo_token(user_id):
    # Query Supabase to get the Expo token for the user
    response = supabase.from_("users").select("expo_token").eq("user_id", user_id).single()
    if response.get("data"):
        return response["data"]["expo_token"]
    return None

# Main process
def main_process():
    # Prompt for face capture first
    voice_prompt("Please show your face.")
    success, face_image_path = capture_image("face_image.jpg")
    if not success:
        print("Failed to capture face image.")
        return

    # Fetch member images from Supabase utils table
    member_images = fetch_member_images()  # Implement this function to get images from Supabase

    # Notify device for approval before proceeding
    socketio.emit('request_approval', {'message': 'Please approve face verification.'})
    
    # Wait for the approval response
    @socketio.on('approval_response')
    def handle_approval_response(data):
        if data.get('status') == 'approved':
            # Proceed with face verification
            face_match_found = False
            for member_image_url in member_images:
                result = compare_face(face_image_path, member_image_url)
                if result.get("match"):
                    face_match_found = True
                    send_notification("Face verification successful.")  #Todo
                    voice_prompt("Face match successful.")
                    break

            if not face_match_found:
                voice_prompt("Face does not match any registered member. Please show your license.")
                
                # Process license image for OCR extraction
                success, license_image_path = capture_image("license_image.jpg")
                if not success:
                    print("Failed to capture license image.")
                    return

                # Process license image for OCR extraction
                license_info = send_license_to_api(license_image_path)
                dob, license_id = license_info.get("dob"), license_info.get("license_id")

                # Authenticate license via public API
                license_image_url, status = authenticate_license(dob, license_id)
                if status != "valid":
                    print("License is not valid.")
                    return

                # Compare face with license image
                result = compare_face(face_image_path, license_image_url)
                if result.get("match"):
                    send_notification(license_id, "License verification successful.")   #Todo
                    print("Face match with license successful.")

                    # Set up periodic monitoring
                    previous_image_path = face_image_path
                    while True:
                        time.sleep(300)  # Wait for 5 minutes
                        success, new_face_image_path = capture_image("new_face_image.jpg")
                        if success:
                            match_result = compare_face(new_face_image_path, previous_image_path)
                            if not match_result.get("match"):
                                voice_prompt("Face does not match. Please show your license again.")
                                main_process()  # Restart process if face does not match
                                break  # Exit the loop
                            previous_image_path = new_face_image_path
                else:
                    print("Face does not match with the license image.")
        else:
            print("Face verification was not approved.")

    # Prompt for face capture first
    voice_prompt("Please show your face.")
    success, face_image_path = capture_image("face_image.jpg")
    if not success:
        print("Failed to capture face image.")
        return

    # Fetch member images from Supabase utils table
    member_images = fetch_member_images()  # Implement this function to get images from Supabase

    # Compare captured face with member images
    face_match_found = False
    for member_image_url in member_images:
        result = compare_face(face_image_path, member_image_url)
        if result.get("match"):
            face_match_found = True
            send_notification("Face verification successful.")  #Todo
            voice_prompt("Face match successful.")
            break

    if not face_match_found:
        voice_prompt("Face does not match any registered member. Please show your license.")
        
        # Process license image for OCR extraction
        success, license_image_path = capture_image("license_image.jpg")
        if not success:
            print("Failed to capture license image.")
            return

        # Process license image for OCR extraction
        license_info = send_license_to_api(license_image_path)
        dob, license_id = license_info.get("dob"), license_info.get("license_id")

        # Authenticate license via public API
        license_image_url, status = authenticate_license(dob, license_id)
        if status != "valid":
            print("License is not valid.")
            return

        # Compare face with license image
        result = compare_face(face_image_path, license_image_url)
        if result.get("match"):
            send_notification(license_id, "License verification successful.")   #Todo
            print("Face match with license successful.")

            # Set up periodic monitoring
            previous_image_path = face_image_path
            while True:
                time.sleep(300)  # Wait for 5 minutes
                success, new_face_image_path = capture_image("new_face_image.jpg")
                if success:
                    match_result = compare_face(new_face_image_path, previous_image_path)
                    if not match_result.get("match"):
                        voice_prompt("Face does not match. Please show your license again.")
                        main_process()  # Restart process if face does not match
                        break  # Exit the loop
                    previous_image_path = new_face_image_path
        else:
            print("Face does not match with the license image.")
    else:
        print("Face match found with registered member.")

    

        previous_image_path = face_image_path
        while True:
            time.sleep(300)  # Wait for 5 minutes
            success, new_face_image_path = capture_image("new_face_image.jpg")
            if success:
                match_result = compare_face(new_face_image_path, previous_image_path)
                if not match_result.get("match"):
                    voice_prompt("Face does not match. Please show your license again.")
                    main_process()  # Restart process if face does not match
                    break  # Exit the loop
                previous_image_path = new_face_image_path
    else:
        print("Face does not match with the license image.")
