import smtplib
from email.mime.text import MIMEText


class Sender:
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def send_email(self, receiver, subject, content):
        # Create Email
        message = MIMEText(content, "html")
        message["Subject"] = subject
        message["From"] = self.email
        message["To"] = receiver
        
        # Connect to Email Server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.email, self.password)
        
        # Send Email
        server.sendmail(self.email, receiver, message.as_string())
        server.quit()
