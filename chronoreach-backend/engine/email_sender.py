import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env from project root (chronoreach-backend/../.env)
from pathlib import Path
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_file, override=True)

class EmailSender:
    def __init__(self):
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        print(f"[EmailSender] MOCK_MODE={self.mock_mode} | SMTP_USER={self.smtp_user}")

    async def send(self, to: str, subject: str, body: str):
        if self.mock_mode:
            print(f"[MOCK EMAIL] To: {to} | Subject: {subject}")
            return True
            
        try:
            msg = MIMEMultipart("alternative")
            msg['Subject'] = subject
            msg['From'] = f"Synaptiq <{self.smtp_user}>"
            msg['To'] = to
            
            # Plain text
            msg.attach(MIMEText(body, "plain"))
            
            # HTML version
            html = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;color:#1e293b">
    <p style="font-size:15px;line-height:1.7">{body.replace(chr(10), '<br>')}</p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:28px 0 16px">
    <p style="font-size:11px;color:#94a3b8;line-height:1.5">
        Sent via <b style="color:#3b82f6">Synaptiq</b> — AI-powered outreach
    </p>
</div>"""
            msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            print(f"[EMAIL SENT] ✅ To: {to} | Subject: {subject}")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] ❌ Failed sending to {to}: {e}")
            return False

email_sender = EmailSender()
