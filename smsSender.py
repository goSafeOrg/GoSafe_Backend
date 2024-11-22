from twilio.rest import Client

def send_sms_to_multiple(message_body):
    account_sid = 'AC79024b1c5db329ffc43797a9ee7fbb37'  # Replace with your Twilio account SID
    auth_token = 'c1a6155e99984e0aae8b7f721a7f4467'    # Replace with your Twilio auth token
    from_number = '+18138565383' # Replace with your Twilio phone number

    # List of recipient phone numbers
    phone_numbers = ["+919618992631","+918520851710"]

    client = Client(account_sid, auth_token)

    for number in phone_numbers:
        try:
            message = client.messages.create(
                to=number,
                from_=from_number,
                body=message_body
            )
            print(f"Message sent successfully to {number} with SID: {message.sid}")
        except Exception as e:
            print(f"Failed to send message to {number}: {e}")

# Usage: Sends to all numbers in the list
send_sms_to_multiple("Hello, how are you !! Do u wana go on a date with me ?")
