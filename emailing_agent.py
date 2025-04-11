import os
import csv
import base64
import pickle
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Files for storing credentials and CSV filename.
CREDENTIALS_FILE = 'credentials.json'
TOKEN_PICKLE = 'token.pickle'
CSV_FILE = 'final_top_candidates.csv'

def get_gmail_service():
    """
    Authenticates with the Gmail API and returns a service resource.
    """
    creds = None
    # Load existing credentials from token.pickle if available.
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next run.
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def create_message(sender, to, subject, message_text):
    """
    Create a message for an email.
    
    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email.
      message_text: The plain text body of the email.
    
    Returns:
      A dictionary containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_message(service, user_id, message):
    """
    Send an email message using the Gmail API.
    
    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. Use "me" to indicate the authenticated user.
      message: Message to be sent.
    
    Returns:
      Sent message.
    """
    sent_message = service.users().messages().send(userId=user_id, body=message).execute()
    print(f"[INFO] Email sent. Message Id: {sent_message['id']}")
    return sent_message

def compose_email(job, candidate_id, reason):
    """
    Compose the email subject and body.
    
    Customize the template as needed.
    """
    subject = f"Interview Invitation for Job {job}"
    body = (
        f"Dear Candidate {candidate_id},\n\n"
        "Congratulations! You have been selected as the top candidate for the position associated with Job "
        f"{job}.\n\n"
        "Interview Details:\n"
        "- Date: [Insert Interview Date]\n"
        "- Time: [Insert Interview Time]\n"
        "- Mode: [Insert Interview Mode e.g., Zoom/Teams/in-person]\n\n"
        f"Reason: {reason}\n\n"
        "Please reply to this email to confirm your attendance or if you have any questions.\n\n"
        "Best regards,\n"
        "Recruitment Team"
    )
    return subject, body

def process_candidates(csv_filename, sender, service):
    """
    Read the CSV and send an interview invitation email to each candidate.
    """
    with open(csv_filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            job = row.get("Job", "Unknown Job")
            candidate_id = row.get("Candidate ID", "Unknown Candidate")
            recipient_email = row.get("Email")
            reason = row.get("Reason", "")
            
            if not recipient_email:
                print(f"[WARN] No email found for Candidate {candidate_id} (Job: {job}). Skipping.")
                continue
            
            subject, body = compose_email(job, candidate_id, reason)
            message = create_message(sender, recipient_email, subject, body)
            try:
                send_message(service, 'me', message)
            except Exception as e:
                print(f"[ERROR] Failed to send email to {recipient_email} for Candidate {candidate_id}: {e}")

def main():
    sender = "your_email@gmail.com"  # Replace with the sender's email address.
    print("[INFO] Authenticating with the Gmail API...")
    service = get_gmail_service()
    print("[INFO] Processing candidates from CSV and sending emails...")
    process_candidates(CSV_FILE, sender, service)
    print("[INFO] All emails processed.")

if __name__ == '__main__':
    main()
