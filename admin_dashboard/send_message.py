from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

client = Client(account_sid, auth_token)


def send_whatsapp_message(number, message):
    try:
        message = client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}',
            body=message,
            to=f'whatsapp:{number}'
        )
        print(f"Message send to number {number}: SID {message.sid}")
    except Exception as e:
        print(f'Failed to send message to {number}: {str(e)}')
