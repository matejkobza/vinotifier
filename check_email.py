#!/usr/bin/env python3
"""
Check SMTP email connection.
Tests if SMTP credentials and connection are working by sending a test email.
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from datetime import datetime

def check_email():
    """Test SMTP connection and send a test email."""

    # Get environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL")

    # Validate environment variables
    if not smtp_user or not smtp_password:
        print("❌ Error: SMTP_USER or SMTP_PASSWORD not set")
        sys.exit(1)

    if not sender_email:
        print("❌ Error: SENDER_EMAIL not set")
        sys.exit(1)

    print(f"🔍 Testing SMTP connection...")
    print(f"   Server: {smtp_server}:{smtp_port}")
    print(f"   User: {smtp_user}")
    print()

    try:
        # Connect to SMTP server
        print("📧 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        print("✅ TLS connection established")

        # Login
        print("🔐 Authenticating...")
        server.login(smtp_user, smtp_password)
        print("✅ Authentication successful")

        # Send test email
        print("📨 Sending test email...")
        subject = "Vinotifier Test Email"
        body = f"""
Hello,

This is a test email from Vinotifier to verify that your email configuration is working correctly.

Test Details:
- Sent at: {datetime.now().isoformat()}
- Server: {smtp_server}
- Port: {smtp_port}

If you received this email, your SMTP configuration is working correctly!

Best regards,
Vinotifier
"""

        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = smtp_user

        server.sendmail(sender_email, [smtp_user], message.as_string())
        print(f"✅ Test email sent successfully to {smtp_user}")

        # Cleanup
        server.quit()
        print("\n✅ SMTP connection test passed!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = check_email()
    sys.exit(0 if success else 1)

