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
            'https://www.googleapis.com/auth/contacts',  # Full access to Contacts
            'https://www.googleapis.com/auth/contacts.other.readonly'  # Access to Other Contacts
        ]
        self.creds = None
        self.service_gmail = None
        self.service_calendar = None
        self.service_contacts = None

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
        self.service_contacts = build('people', 'v1', credentials=self.creds)
        
        print("Authentication successful!")
        return True

    def create_event(self, title, location, description, start_time, end_time, attendees=None):
        """Creates a calendar event.
        
        Args:
            title (str): Title of the event
            location (str): Location of the event
            description (str): Event description
            start_time (datetime): Start time of the event
            end_time (datetime): End time of the event
            attendees (list): Optional list of attendee email addresses
        """
        try:
            event = {
                'summary': title,
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
    
    def list_contacts(self, page_size=100):
        """Lists the user's contacts.
        
        Args:
            page_size (int): Number of contacts to return per page
        """
        try:
            results = self.service_contacts.people().connections().list(
                resourceName='people/me',
                pageSize=page_size,
                personFields='names,emailAddresses,phoneNumbers'
            ).execute()
            connections = results.get('connections', [])
            
            contacts = []
            for person in connections:
                contact_info = {
                    'resourceName': person.get('resourceName', '')
                }
                
                # Get name
                names = person.get('names', [])
                if names:
                    contact_info['name'] = names[0].get('displayName', '')
                
                # Get email addresses
                emails = person.get('emailAddresses', [])
                if emails:
                    contact_info['email'] = emails[0].get('value', '')
                
                # Get phone numbers
                phones = person.get('phoneNumbers', [])
                if phones:
                    contact_info['phone'] = phones[0].get('value', '')
                
                contacts.append(contact_info)
            
            return contacts
        except Exception as e:
            print(f'An error occurred: {e}')
            return []
    
    def list_frequent_contacts(self, page_size=100):
        """Lists other contacts (people you've interacted with but haven't added).
        
        This includes people you've communicated with in Gmail or other Google services.
        """
        try:
            print("Fetching frequent contacts...")
            results = self.service_contacts.otherContacts().list(
                pageSize=page_size,
                readMask='names,emailAddresses,phoneNumbers'
            ).execute()
            
            print(f"Found {len(results.get('otherContacts', []))} frequent contacts")
            
            contacts = []
            for person in results.get('otherContacts', []):
                contact_info = {}
                
                # Get name
                names = person.get('names', [])
                if names:
                    contact_info['name'] = names[0].get('displayName', '')
                
                # Get email addresses
                emails = person.get('emailAddresses', [])
                if emails:
                    contact_info['email'] = emails[0].get('value', '')
                
                # Get phone numbers
                phones = person.get('phoneNumbers', [])
                if phones:
                    contact_info['phone'] = phones[0].get('value', '')
                
                if contact_info:  # Only add if we found some info
                    contacts.append(contact_info)
            
            return contacts
        except Exception as e:
            print(f'An error occurred: {e}')
            print(f'Error details: {str(e)}')
            return []

    def create_contact(self, name, email=None, phone=None):
        """Creates a new contact.
        
        Args:
            name (str): Contact's full name
            email (str, optional): Contact's email address
            phone (str, optional): Contact's phone number
        """
        try:
            body = {
                'names': [
                    {
                        'givenName': name
                    }
                ]
            }
            
            if email:
                body['emailAddresses'] = [
                    {
                        'value': email
                    }
                ]
            
            if phone:
                body['phoneNumbers'] = [
                    {
                        'value': phone
                    }
                ]
            
            result = self.service_contacts.people().createContact(
                body=body
            ).execute()
            
            print(f"Contact created: {result.get('names', [{}])[0].get('displayName', '')}")
            return result
        except Exception as e:
            print(f'An error occurred: {e}')
            return None
    
    def get_contact_metrics(self, email, days_back=720):
        """Get interaction metrics for a specific contact."""
        try:
            metrics = {
                'email': email,
                'emails_received': 0,
                'emails_sent': 0,
                'meetings': 0,
                'last_interaction': None
            }
            
            # Calculate date range
            now = datetime.now(timezone.utc)
            start_date = (now - timedelta(days=days_back))
            formatted_date = start_date.strftime('%Y/%m/%d')  # Gmail query format
            
            print(f"\nAnalyzing interactions with: {email}")
            print(f"Looking back to: {formatted_date}")
            
            # Get received emails with pagination
            received_query = f'from:({email}) after:{formatted_date}'
            print(f"Executing received query: {received_query}")
            
            received_messages = []
            next_page_token = None
            while True:
                received_results = self.service_gmail.users().messages().list(
                    userId='me',
                    q=received_query,
                    pageToken=next_page_token
                ).execute()
                
                if 'messages' in received_results:
                    received_messages.extend(received_results['messages'])
                    print(f"Found {len(received_messages)} received emails so far...")
                
                next_page_token = received_results.get('nextPageToken')
                if not next_page_token:
                    break
            
            metrics['emails_received'] = len(received_messages)
            print(f"Total received emails: {metrics['emails_received']}")
            
            # Get sent emails with pagination
            sent_query = f'to:({email}) after:{formatted_date}'
            print(f"Executing sent query: {sent_query}")
            
            sent_messages = []
            next_page_token = None
            while True:
                sent_results = self.service_gmail.users().messages().list(
                    userId='me',
                    q=sent_query,
                    pageToken=next_page_token
                ).execute()
                
                if 'messages' in sent_results:
                    sent_messages.extend(sent_results['messages'])
                    print(f"Found {len(sent_messages)} sent emails so far...")
                
                next_page_token = sent_results.get('nextPageToken')
                if not next_page_token:
                    break
            
            metrics['emails_sent'] = len(sent_messages)
            print(f"Total sent emails: {metrics['emails_sent']}")
            
            # Track latest interaction timestamp
            latest_timestamp = None
            
            # Get last email interaction
            all_messages = received_messages + sent_messages
            if all_messages:
                # Sort by ID (Gmail IDs are chronological)
                all_messages.sort(key=lambda x: x['id'], reverse=True)
                latest_message = self.service_gmail.users().messages().get(
                    userId='me',
                    id=all_messages[0]['id']
                ).execute()
                latest_timestamp = datetime.fromtimestamp(
                    int(latest_message['internalDate'])/1000,
                    tz=timezone.utc
                )
            
            try:
                # Get calendar metrics
                events_result = self.service_calendar.events().list(
                    calendarId='primary',
                    timeMin=start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    timeMax=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                # Track meetings and find latest calendar interaction
                latest_event_time = None
                for event in events_result.get('items', []):
                    attendees = event.get('attendees', [])
                    if any(attendee.get('email') == email for attendee in attendees):
                        metrics['meetings'] += 1
                        # Check end time of event
                        event_end = event.get('end', {}).get('dateTime')
                        if event_end:
                            event_time = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                            if latest_event_time is None or event_time > latest_event_time:
                                latest_event_time = event_time
                
                print(f"Found {metrics['meetings']} calendar events")
                
                # Compare email and calendar timestamps
                if latest_event_time:
                    if latest_timestamp is None or latest_event_time > latest_timestamp:
                        latest_timestamp = latest_event_time
                
            except Exception as calendar_error:
                print(f"Calendar error: {calendar_error}")
                metrics['meetings'] = 0
            
            # Set the final last interaction time
            if latest_timestamp:
                metrics['last_interaction'] = latest_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            return metrics
            
        except Exception as e:
            print(f'An error occurred getting metrics: {e}')
            print(f'Error details: {str(e)}')
            return None

    def analyze_frequent_contacts(self, top_n=10, days_back=720):
        """Analyze interaction patterns with frequent contacts.
        
        Args:
            top_n (int): Number of top contacts to analyze
            days_back (int): Number of days to look back
        """
        try:
            print(f"\nAnalyzing top {top_n} frequent contacts over past {days_back} days...")
            contacts = self.list_frequent_contacts(page_size=top_n)
            
            detailed_contacts = []
            for contact in contacts:
                if 'email' in contact:
                    metrics = self.get_contact_metrics(contact['email'], days_back)
                    if metrics:
                        detailed_contacts.append({
                            'name': contact.get('name', 'N/A'),
                            **metrics
                        })
                        
                        print(f"\nContact: {contact.get('name', 'N/A')}")
                        print(f"Email: {metrics['email']}")
                        print(f"Emails received: {metrics['emails_received']}")
                        print(f"Emails sent: {metrics['emails_sent']}")
                        print(f"Meetings: {metrics['meetings']}")
                        print(f"Last interaction: {metrics['last_interaction']}")
                        
            return detailed_contacts
            
        except Exception as e:
            print(f'An error occurred analyzing contacts: {e}')
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
    

def authenticate():
    google_api = GoogleAPI()
    google_api.authenticate()


if __name__ == '__main__':
    authenticate()
