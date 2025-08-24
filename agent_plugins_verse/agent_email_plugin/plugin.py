# email_plugin.py
import os
import smtplib
from email.mime.text import MIMEText
from semantic_kernel.functions import kernel_function
from dotenv import load_dotenv
load_dotenv()

class EmailPlugin:
    def __init__(self):
        self.sender = os.getenv("SENDER_EMAIL")
        self.app_password = os.getenv("GMAIL_PASSWORD")

    @kernel_function(
        name="send_email",
        description="Send an email to a specific recipient using Gmail SMTP."
    )
    def send_email(
        self,
        subject: str,
        body: str,
        recipient: str = "pmadhan0006@gmail.com"
    ) -> str:
        """
        Sends an email using Gmail SMTP.

        Args:
            subject (str): Subject line of the email
            body (str): Body content of the email
            recipient (str): Recipient email address

        Returns:
            str: Success or failure message
        """
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = recipient

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.sender, self.app_password)
                smtp.sendmail(self.sender, [recipient], msg.as_string())

            return f"✅ Email sent to {recipient} with subject '{subject}'."
        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"
