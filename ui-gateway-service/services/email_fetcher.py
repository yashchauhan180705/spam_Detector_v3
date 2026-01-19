"""
Email Fetcher Service - Handles IMAP email fetching.
Extracted from the original frontend-service for the UI Gateway.
"""
import imaplib
import email
from email.header import decode_header
import ssl
import socket
import re


def clean_text(text):
    """Clean email text for better processing."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = ' '.join(text.split())  # Normalize whitespace
    return text


def decode_mime_words(s):
    """Decode MIME encoded words."""
    if s is None:
        return ""
    decoded_parts = []
    for part, encoding in decode_header(s):
        if isinstance(part, bytes):
            try:
                if encoding:
                    part = part.decode(encoding)
                else:
                    part = part.decode('utf-8', errors='ignore')
            except Exception:
                part = part.decode('utf-8', errors='ignore')
        decoded_parts.append(str(part))
    return ''.join(decoded_parts)


def fetch_emails(email_address, password, imap_server, port=993, max_emails=50):
    """
    Fetch emails from IMAP server.

    Returns:
        tuple: (success: bool, result: list|str)
               On success, result is a list of email dicts
               On failure, result is an error message
    """
    try:
        # Increase timeout for large batches: base 30s + 0.5s per email
        timeout = int(max(30, 30 + max_emails * 0.5))
        socket.setdefaulttimeout(timeout)

        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(imap_server, port, ssl_context=context)

        try:
            mail.login(email_address, password)
        except imaplib.IMAP4.error as login_error:
            error_msg = str(login_error)
            if "Application-specific password required" in error_msg or "ALERT" in error_msg:
                return False, "Gmail requires App-Specific Password"
            elif "authentication failed" in error_msg.lower():
                return False, "Authentication failed. Check your credentials"
            else:
                return False, f"Login failed: {error_msg}"

        status, _ = mail.select('inbox')
        if status != 'OK':
            return False, "Failed to select inbox"

        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return False, "Failed to search emails"

        message_ids = messages[0].split()
        if not message_ids:
            return False, "No emails found"

        message_ids = message_ids[-max_emails:]
        emails_data = []

        for msg_id in message_ids:
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    continue

                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                subject = decode_mime_words(email_message["Subject"]) or "No Subject"
                sender = decode_mime_words(email_message["From"]) or "Unknown"
                receiver = decode_mime_words(email_message["To"]) or email_address
                date_str = email_message["Date"] or ""
                message_id = email_message["Message-ID"] or str(msg_id)

                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                            except Exception:
                                continue
                else:
                    try:
                        content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        content = str(email_message.get_payload())

                content = clean_text(content)

                emails_data.append({
                    'id': message_id,
                    'subject': subject[:100] + "..." if len(subject) > 100 else subject,
                    'sender': sender,
                    'receiver': receiver,
                    'date': date_str,
                    'preview': content[:200] + "..." if len(content) > 200 else content,
                    'full_content': content,
                    'prediction': None,
                    'feedback': None
                })

            except Exception:
                continue

        mail.close()
        mail.logout()

        if not emails_data:
            return False, "No emails could be processed"

        return True, emails_data

    except Exception as e:
        return False, f"Error fetching emails: {str(e)}"

