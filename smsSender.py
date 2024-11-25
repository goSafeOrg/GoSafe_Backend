from twilio.rest import Client

def send_sms_twilio(recipient_number, message_body):
    """
    Sends an SMS using Twilio.

    :param recipient_number: The recipient's phone number (in E.164 format, e.g., +1234567890).
    :param message_body: The SMS content.
    :return: The SID of the sent message.
    """
    # Twilio credentials (replace with your actual credentials)
    account_sid = 'AC79024b1c5db329ffc43797a9ee7fbb37'  # Replace with your Account SID
    auth_token = '87a9916966a4c35f2edac78cfb8039dc'  # Replace with your Auth Token
    sender_number = "+18138565383"  # Replace with your Twilio phone number

    try:
        # Initialize the Twilio Client
        client = Client(account_sid, auth_token)

        # Send the SMS
        message = client.messages.create(
            to=recipient_number,
            from_=sender_number,
            body=message_body
        )

        # Print and return the Message SID
        print(f"Message sent! SID: {message.sid}")
        return message.sid

    except Exception as e:
        print(f"Failed to send message: {e}")
        return None

# Example Usage
if __name__ == "__main__":
    # Recipient phone number
    recipient = "+919618992631"  # Replace with the recipient's phone number

    # Message content
    message = "Hello homie!"

    # Send the message
    send_sms_twilio(recipient, message)
