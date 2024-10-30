# Main process
def main_process():
    # Prompt for face capture first
    voice_prompt("Please show your face.")
    success, face_image_path = capture_image("face_image.jpg")
    if not success:
        print("Failed to capture face image.")
        return

    # Fetch member images from Supabase utils table
    member_images = fetch_member_images()

    # Compare captured face with member images
    face_match_found = False
    matched_user_id = None  # Store the matched user ID for notification purposes

    for member_image_url in member_images:
        result = compare_face(face_image_path, member_image_url)
        if result.get("match"):
            face_match_found = True
            matched_user_id = member_image_url.split('/')[-1]  # Extract the user ID or relevant identifier
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
            voice_prompt("License verification successful.")

            # Here, send notification with user details and wait for approval
            user_details = {
                "name": "User Name",  # Replace with actual user name or details
                "license_id": license_id,
                "status": "Pending",
                "image_url": license_image_url  # Assuming this is the image URL to send
            }
            send_notification(matched_user_id, "License verification successful.", **user_details)

            # Wait for approval from the user
            approval_received = False

            # Function to handle incoming SocketIO events for approval
            def handle_approval(data):
                nonlocal approval_received
                if data.get('approved'):
                    approval_received = True

            # Set up SocketIO event listener for approval
            socketio.on_event('approval_event', handle_approval)

            # Wait for approval (or timeout after a set duration)
            timeout_duration = 60  # Timeout after 60 seconds
            start_time = time.time()

            while not approval_received and (time.time() - start_time < timeout_duration):
                socketio.sleep(1)  # Sleep for a while before checking again

            # Remove the event listener after checking for approval
            socketio.off_event('approval_event', handle_approval)

            if approval_received:
                voice_prompt("Approval received. Identity confirmed.")
                print("Identity confirmed.")
                # Proceed with further actions here...
            else:
                voice_prompt("Approval not received in time.")
                print("Approval not received. Please try again.")
        else:
            voice_prompt("Face does not match with the license image.")
            print("Face does not match with the license image.")
    else:
        voice_prompt("Face match found with registered member.")
        print("Face match found with registered member.")
``