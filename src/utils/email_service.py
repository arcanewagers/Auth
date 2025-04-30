# src/utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
from src.utils.config import settings

class EmailService:
    def __init__(self):
        self.smtp_server="smtp.gmail.com"
        self.port = 465  # TLS port
        self.sender_email = settings.EMAIL_SENDER
        self.sender_password = settings.EMAIL_PASSWORD
    def send_email(self, to_email: str, subject: str, html_content: str):
        """
        Send an email using Google SMTP
        """
        # Create a multipart message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = to_email

        # Convert HTML content to MIMEText
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Create secure context
        context = ssl.create_default_context()

        try:
            # Use SSL context and SMTP_SSL instead of starttls
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=ssl.create_default_context()) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email, 
                    to_email, 
                    message.as_string()
                )
        except Exception as e:
            # Log the error - you'll want to add proper logging
            print(f"Error sending email: {e}")
            raise

    