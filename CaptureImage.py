import cv2
import requests
import time
import pyttsx3
from datetime import datetime
import os
import json
from PIL import Image, ImageOps
from supabase import create_client, Client
import os

# Set up Supabase client
SUPABASE_URL = "https://igbtezppidteqhbauxlv.supabase.co"  # Add your Supabase URL here or set it as an environment variable
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlnYnRlenBwaWR0ZXFoYmF1eGx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkxODU5MDUsImV4cCI6MjA0NDc2MTkwNX0.MnP_05Bb5fA4G3DEyzeO4KmU6xVkyazj6ruzosPZyJk"  # Add your Supabase API key here or set it as an environment variable
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



import socketio
deviceId='Abc1'
USER_ID='58ad8e22-442c-4517-81ca-01344c5b68f9'
# Create a Socket.IO client instance
socketio = socketio.Client()

# Define event handlers
@socketio.event
def connect():
    print("Connected to the server")
     
    socketio.emit("joinRoom", {"roomId": deviceId})
    print(f"Joined room with device ID: {deviceId}")

@socketio.event
def disconnect():
    print("Disconnected from the server")

@socketio.event
def connect_error(data):
    print("Connection failed:", data)

def connectSocket(url="http://13.201.153.161:5005"):
    try:
        socketio.connect(url)
        print("Socket connected successfully")
    except Exception as e:
        print("Error connecting to socket:", e)







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
        # Fetch file list from Supabase bucket
        folder_path = f"profiles/{USER_ID}/members"
        files = supabase.storage.from_("user-images").list(folder_path)
        
        if files:
            member_image_urls = [file['name'] for file in files]

            # Download and cache each member image
            for image_name in member_image_urls:
                image_url = f"{SUPABASE_URL}/storage/v1/object/public/user-images/{folder_path}/{image_name}"
                image_response = requests.get(image_url)
                if image_response.ok:
                    image_path = os.path.join(CACHE_DIR, image_name+'.jpg')
                    with open(image_path, 'wb') as f:  
                        f.write(image_response.content)
                else:
                    print(f"Failed to download image from {image_url}")

            return [os.path.join(CACHE_DIR, image_name) for image_name in member_image_urls]
        else:
            print("No images found in the specified Supabase folder")
    except Exception as e:
        print(f"Error fetching member images: {e}")

    return []
   

# Capture and save an image from the webcam
def capture_image(image_name):
    # Open the webcam
    cap = cv2.VideoCapture(0)

    # Allow the camera to initialize and capture a frame
   
    success, img = cap.read()
    
    if success:
        # Display the captured frame in a window
        cv2.imshow("Captured Image", img)
        
        # Save the captured image to the specified file name
        cv2.imwrite(image_name, img)
        
        # Wait for a short time or until a key is pressed to close the window
        cv2.waitKey(1000)  # 1000 ms (1 second) delay, adjust as needed
        cv2.destroyAllWindows()  # Close the image display window

    # Release the webcam
    cap.release()

    return success, image_name



def send_license_to_api(image_path):
  
  
    url = 'http://13.201.153.161:5000/upload'
    with open(
        image_path, 'rb') as image_file:
        files = {'file': image_file}
        response = requests.post(url, files=files)
    
    return response.json()

# Authenticate license and retrieve license image
def authenticate_license(dob, license_id):
    # url = f'http://public-api/license/validate?dob={dob}&license_id={license_id}'
    # response = requests.get(url)
    # if response.status_code == 200:
    #     data = response.json()
    #     return data.get('image_url'), data.get('status')  # Image URL and status
    return {'img':'license_photo.jpg', 'status':'Valid','name':'nikhil','license_id':license_id}

# Send captured face to comparison API
def compare_face(image_path, license_image_path):
    url = 'http://13.201.153.161:5000/compare_faces'
    with open(image_path, 'rb') as image_file1, open(license_image_path, 'rb') as image_file2:
        files = {
            'image1': image_file1,
            'image2': image_file2
        }
        response = requests.post(url, files=files)

    return response.json()
# Send notification to user
def send_notification(user_id, message, name, from_user, license_id, description, image_url, status="Pending"):
    # Step 1: Retrieve the Expo token for push notification
    expo_token = get_user_expo_token(user_id)
    print(image_url)
    # Step 2: Insert notification details into the notifications table
    data = (supabase.table("notifications").insert({
        "name": name,
        "from": from_user,
        "license_id": license_id,
        "description": description,
        "image": image_url,
        "status": status,
      
    }).execute()
    )

    # Check if notification was inserted successfully and retrieve its ID
    if data.data:
        notification_id = data.data[0]["id"]
        
        # Step 3: Update the utility table to add this notification ID under the user
        response = (supabase.from_("utility").select("notifications").eq("userId", user_id).single().execute())
    
        if  response.data:
            existing_notifications = response.data.get("notifications", [])
        
        # Step 2: Append the new notification_id to the list
            updated_notifications = existing_notifications + [notification_id]
        
        # Step 3: Update the utility table with the new list of notifications
            utility_response = (supabase.from_("utility").update({
            "notifications": updated_notifications
        }).eq("userId", user_id).execute())
        
            if utility_response.data:
                print("Notification updated successfully.")
            else:
                 print("Failed to update utility table:", utility_response.get("error"))
        else:
            print("Failed to fetch existing notifications:", response.get("error"))

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
                print('successfully sent push notification')
                # log_verification_event(user_id, "Notification Sent", message)
            else:
                print("Failed to send push notification:", push_response.text)
                
        # Log success of adding notification to utility table
        if utility_response.data :
          print(user_id, "Notification Added to Utility", f"Notification ID {notification_id}")
        else:
            print("Failed to update utility table:", utility_response.get("error"))
            
    else:
        print("Failed to add notification:", data.get("error"))


# Get user Expo token from database (Mock function)
import json

def get_user_expo_token(user_id):
    # Query Supabase to get the Expo token for the user
    response = supabase.from_("Users").select("expo_token").eq("id", user_id).single().execute()
    
    # Convert response to string
    response_str = str(response)
    print("Response as string:", response_str)

    # Parse response to JSON and check for expo_token
    try:
      
    
        if  "expo_token" in response_str:
            expo_token = response_str.split(':')[1].split('}')[0][2:-1]
            print("Expo token retrieved:", expo_token)
            return expo_token
    except json.JSONDecodeError as e:
        print("Failed to decode JSON:", e)
    
    print("Expo token not found or error in response format.")
    return None

import threading

# Function to listen for the status response
def listen_for_status_response():
    @socketio.on("getStatus")
    def handle_status_response(data):
        print("Status Response Received:", data)
        # Set the status based on the response
        global status_response
        status_response = data["status"]  # Update global status response
        # Optionally, you can emit an event or trigger other actions based on the response



# Main process
global status_response
status_response = None  # Initialize the status response
def main_process():
    # Connect to the socket and prompt user to show face

    connectSocket()
    voice_prompt("Please show your face.")

    # Capture the initial face image
    success, face_image_path = capture_image("face_image.jpg")
    if not success:
        print("Failed to capture face image.")
        return

    # # Fetch member images from Supabase utils table
    member_images = fetch_member_images()  # Get images from Supabase
    print(member_images)

    # # Compare captured face with member images
    face_match_found = False
    for member_image_url in member_images:
        result = compare_face(face_image_path, member_image_url)
        print(result)
    
        if result.get("match"):
            face_match_found = True
            user_id = USER_ID  # Replace with the actual user ID or retrieve accordingly
            name = member_image_url.split('\\')[1].split('.')[0].split('-')[0]  
            from_user = deviceId  # Or specify who the notification is from
            license_id =member_image_url.split('\\')[1].split('.')[0].split('-')[1]  
            description = "Face matched with registered member."
            image_url = f'{SUPABASE_URL}/storage/v1/object/public/user-images/profiles/{USER_ID}/members/'+member_image_url.split('\\')[1]  # URL of the matched member image
            message = "Face verification successful."
            status = "Pending"

            send_notification(
                user_id=user_id,
                message=message,
                name=name,
                from_user=from_user,
                license_id=license_id,
                description=description,
                image_url=image_url,
                status=status
            )
        
            voice_prompt("Face match successful.")
        
            break
      
    if(face_match_found):
        voice_prompt("Please wait for approval")
        while status_response is None:
            socketio.sleep(0.1)  # This keeps the event loop running

                # Now you can handle the approval/rejection
            if status_response == "Accepted":
                    voice_prompt("Face verification approved.")
                    break
            elif status_response == "Rejected":
                voice_prompt("Face verification rejected.")
                     # Additional actions for rejected status
            


# Start listening for status responses in a separate thread


    if not face_match_found:
        voice_prompt("Face does not match any registered member. Please show your license.")

        # Capture license image for OCR extraction
        time.sleep(2)

        voice_prompt(" Please keep your license still.")
        # success, license_image_path = capture_image("license_image.jpg")
        success, license_image_path= True ,"license_image.jpg"
        if not success:
            print("Failed to capture license image.")
            return

        # Extract license information via OCR
        license_info = send_license_to_api(license_image_path)
        # print(license_info,license_info["data"])
        dob, license_id = license_info['data']['dob'], license_info['data']['licnese_no']
        print(dob,license_id)

    #     # Authenticate license via public API
        license_data = authenticate_license(dob, license_id)
        if license_data['status']!= "Valid":
            voice_prompt("License is not valid.")
            return

    #     # Compare face with license image
        result = compare_face(face_image_path, license_data['img'])
        if result.get("match"):
            
            user_id = USER_ID  # Replace with the actual user ID or retrieve accordingly
            name = license_data['name'] 
            from_user = deviceId  # Or specify who the notification is from
            license_id =license_data['license_id'] 
            description = "Face matched with registered member."
            image_url = 'https://picsum.photos/id/1/200/300'
            message = "Face verification successful."
            status = "Pending"

            send_notification(
                user_id=user_id,
                message=message,
                name=name,
                from_user=from_user,
                license_id=license_id,
                description=description,
                image_url=image_url,
                status=status
            )
        
         
            voice_prompt("Face verification with license successful.")
            voice_prompt("Please wait for approval")
           
            while status_response is None:
                socketio.sleep(0.1)  # This keeps the event loop running
                print(status_response,'kjhgfd')
                    # Now you can handle the approval/rejection
                if status_response == "Accepted":
                        voice_prompt("Face verification approved.")
                        break
                elif status_response == "Rejected":
                    voice_prompt("Face verification rejected.")
                        # Additional actions for rejected status

         
    #         # Set up periodic monitoring
            previous_image_path = face_image_path
            while True:
                time.sleep(100)  
                success, new_face_image_path = capture_image("new_face_image.jpg")
                if success:
                    match_result = compare_face(new_face_image_path, previous_image_path)
                    if not match_result.get("match"):
                        voice_prompt("Face does not match. Please show your license again.")
                        main_process()  # Restart process if face does not match
                        break
                    previous_image_path = new_face_image_path
        else:
            print("Face does not match with the license image.")
            socketio.emit('approval_notification', {'status': 'rejected', 'message': 'Face did not match with license'})

    # else:
    #     print("Face match found with registered member.")

threading.Thread(target=listen_for_status_response, daemon=True).start()
main_process()