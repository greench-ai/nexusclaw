"""
NexusClaw Email Notifications
Send emails via SMTP (Gmail, SMTP2GO, etc.) or webhooks.
"""
import os, smtplib, json, asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional
import aiohttp

@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_name: str = "NexusClaw"
    use_tls: bool = True

class EmailNotifier:
    """
    Send email notifications.
    Supports: SMTP (Gmail, SMTP2GO, etc.), webhook (SendGrid, Mailgun, etc.)
    """
    
    def __init__(self, config_path: str = "~/.nexusclaw/email_config.json"):
        self.config_path = os.path.expanduser(config_path)
        self.config: Optional[EmailConfig] = None
        self._load()
    
    def _load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                d = json.load(f)
                self.config = EmailConfig(**d)
    
    def configure(self, smtp_host: str, smtp_port: int, smtp_user: str, 
                  smtp_password: str, from_name: str = "NexusClaw", use_tls: bool = True):
        self.config = EmailConfig(smtp_host, smtp_port, smtp_user, smtp_password, from_name, use_tls)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.config.__dict__, f, indent=2)
    
    def send_sync(self, to: str, subject: str, body: str, html: str = None) -> dict:
        """Send email synchronously."""
        if not self.config:
            return {"ok": False, "error": "Email not configured. Run: nexusclaw email --setup"}
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.smtp_user}>"
            msg["To"] = to
            
            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            
            if self.config.use_tls:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(self.config.smtp_user, to, msg.as_string())
            server.quit()
            
            return {"ok": True, "to": to, "subject": subject}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def send(self, to: str, subject: str, body: str, html: str = None) -> dict:
        """Async wrapper."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.send_sync(to, subject, body, html))
    
    # Convenience methods
    async def password_found(self, container: str, wallet: str):
        """Notify when BTC password is found."""
        return await self.send(
            to="greench",
            subject=f"🔓 BTC Password Found! ({container})",
            body=f"""A Bitcoin wallet password was found!

Container: {container}
Wallet: {wallet}

Check the container immediately:
docker logs {container}

Then import the wallet to check the balance.

— NexusClaw BTC Recovery Alert"""
        )
    
    async def attack_complete(self, container: str, wallet: str, found: bool):
        """Notify when an attack completes."""
        if found:
            await self.password_found(container, wallet)
        else:
            print(f"Attack {container} completed — password not found")
    
    async def heartbeat_alert(self, count: int, message: str):
        """Send heartbeat alert."""
        return await self.send(
            to="greench",
            subject=f"⚠️ NexusClaw Alert #{count}",
            body=f"Heartbeat {count}: {message}"
        )

def cli_setup():
    """Interactive email setup."""
    print("\n📧 NexusClaw Email Setup\n")
    host = input("SMTP Host [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
    port = int(input("SMTP Port [465]: ").strip() or "465")
    user = input("SMTP User: ").strip()
    password = input("SMTP Password: ").strip()
    from_name = input("From Name [NexusClaw]: ").strip() or "NexusClaw"
    
    notifier = EmailNotifier()
    notifier.configure(host, port, user, password, from_name)
    print("\n✅ Email configured!")
    
    # Test
    test = input("\nSend test email? (y/n): ").strip().lower() == "y"
    if test:
        to = input("To email: ").strip()
        result = asyncio.run(notifier.send(to, "NexusClaw Test", "Email is working!"))
        print("✅ Test sent!" if result["ok"] else f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        cli_setup()
    else:
        print("Usage: python3 email.py --setup")
