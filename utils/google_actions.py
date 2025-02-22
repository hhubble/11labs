from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime, timedelta, timezone


class GoogleAPI:
    def __init__(self):
        self.SCOPES = [
            'https://mail.google.com/',  # Full access to Gmail
            'https://www.googleapis.com/auth/calendar',  # Full access to Calendar
        ]
        self.creds = None
        self.service_gmail = None
        self.service_calendar = None

    def authenticate(self):
        """Handles the OAuth 2.0 authentication flow."""
        # Check if token.pickle exists with stored credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        # If credentials are invalid or don't exist, let's get new ones
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        # Build both services
        self.service_gmail = build('gmail', 'v1', credentials=self.creds)
        self.service_calendar = build('calendar', 'v3', credentials=self.creds)
        print("Authentication successful!")

    def create_event(self, summary, location, description, start_time, end_time, attendees=None):
        """Creates a calendar event.
        
        Args:
            summary (str): Title of the event
            location (str): Location of the event
            description (str): Event description
            start_time (datetime): Start time of the event
            end_time (datetime): End time of the event
            attendees (list): Optional list of attendee email addresses
        """
        try:
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            event = self.service_calendar.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Sends email notifications to attendees
            ).execute()

            print(f'Event created: {event.get("htmlLink")}')
            return event
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def list_messages(self, max_results=10):
        """Lists the user's Gmail messages."""
        try:
            results = self.service_gmail.users().messages().list(
                userId='me', maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def get_message(self, msg_id):
        """Gets a specific message by ID."""
        try:
            message = self.service_gmail.users().messages().get(
                userId='me', id=msg_id
            ).execute()
            return message
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def send_email(self, to, subject, body):
        """Sends an email using Gmail API.
        
        Args:
            to (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body content
        """
        try:
            from email.mime.text import MIMEText
            import base64
            
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the message
            sent_message = self.service_gmail.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"Message Id: {sent_message['id']}")
            return sent_message
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

def send_test_email():
    google_api = GoogleAPI()
    google_api.authenticate()
    google_api.send_email(
        to="haz@pally.com",
        subject="Test Email",
        body="This is a test email!"
    )
    
def create_test_event():
    google_api = GoogleAPI()
    google_api.authenticate()
    
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    google_api.create_event(
        summary='11Labs Agent Test',
        location='Founders, Inc',
        description='Testing',
        start_time=start_time,
        end_time=end_time,
        attendees=['haz@pally.com', 'wylansford@gmail.com']
    )
    
    
if __name__ == '__main__':
    send_test_email()
