import imaplib
import email
import json
import base64
import os
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass, field
from app.core.logger import logger
from app.ai.llm.ollama_client import ollama_client
from app.core.guardian import guardian_engine, DisagreementLevel
from email.header import decode_header
from typing import Optional

@dataclass
class EmailMessage:
    email_id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    received_at: datetime
    priority: str
    draft_response: Optional[str] = None
    draft_status: str = "pending"
    read: bool = False

@dataclass
class EmailAccount:
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool = True

class EmailAgent:
    def __init__(self):
        self.config_file = "data/email_config.json"
        self.account: Optional[EmailAccount] = None
        self.emails: list[EmailMessage] = []
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    password = base64.b64decode(data.get("password", "").encode()).decode()
                    self.account = EmailAccount(
                        host=data.get("host"),
                        port=data.get("port"),
                        username=data.get("username"),
                        password=password,
                        use_ssl=data.get("use_ssl", True)
                    )
            except Exception as e:
                logger.error(f"Failed to load email config: {e}")

    def configure(self, host: str, port: int, username: str, password: str, use_ssl: bool = True):
        self.account = EmailAccount(host, port, username, password, use_ssl)
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        try:
            with open(self.config_file, "w") as f:
                json.dump({
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": base64.b64encode(password.encode()).decode(),
                    "use_ssl": use_ssl
                }, f)
        except Exception as e:
            logger.error(f"Failed to save email config: {e}")

    def is_configured(self) -> bool:
        return self.account is not None

    def _get_connection(self):
        if not self.account:
            return None
        try:
            if self.account.use_ssl:
                mail = imaplib.IMAP4_SSL(self.account.host, self.account.port)
            else:
                mail = imaplib.IMAP4(self.account.host, self.account.port)
            mail.login(self.account.username, self.account.password)
            return mail
        except Exception as e:
            logger.error(f"IMAP Connection failed: {e}")
            return None

    async def fetch_emails(self, limit: int = 20) -> list[EmailMessage]:
        if not self.is_configured():
            return []
        
        mail = self._get_connection()
        if not mail:
            return []

        try:
            mail.select('inbox')
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            recent_ids = email_ids[-limit:]
            
            new_emails = []
            for e_id in recent_ids:
                status, msg_data = mail.fetch(e_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg.get("Subject", ""))[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                        
                        from_addr = msg.get("From", "")
                        to_addr = msg.get("To", "")
                        
                        # Get body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    try:
                                        body = part.get_payload(decode=True).decode(errors="ignore")
                                        break
                                    except:
                                        pass
                        else:
                            content_type = msg.get_content_type()
                            if content_type == "text/plain" or content_type == "text/html":
                                try:
                                    body = msg.get_payload(decode=True).decode(errors="ignore")
                                except:
                                    pass
                        
                        # Just basic timestamp fallback
                        received_at = datetime.now()
                        
                        # Basic classification to start with
                        email_msg = EmailMessage(
                            email_id=str(uuid4()),
                            from_addr=from_addr,
                            to_addr=to_addr,
                            subject=subject,
                            body=body,
                            received_at=received_at,
                            priority="fyi"
                        )
                        email_msg.priority = await self.classify_email(email_msg)
                        new_emails.append(email_msg)
                        
            self.emails.extend(new_emails)
            return new_emails
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

    async def classify_email(self, email_msg: EmailMessage) -> str:
        body_lower = email_msg.body.lower()
        subject_lower = email_msg.subject.lower()
        
        # Heuristics
        if "unsubscribe" in body_lower or "viagra" in body_lower or "casino" in body_lower:
            return "spam"
        if "invite" in subject_lower or "calendar" in body_lower:
            return "fyi"
        if "?" in subject_lower or "can you" in body_lower:
            return "needs_response"
            
        # Try LLM
        if await ollama_client.is_available():
            try:
                prompt = f"Classify this email into one of: urgent, needs_response, fyi, spam. Reply ONLY with the classification.\nSubject: {email_msg.subject}\nBody: {email_msg.body}"
                res = await ollama_client.chat([{"role": "user", "content": prompt}], model="qwen2.5:1.5b")
                ans = res.lower().strip()
                for p in ["urgent", "needs_response", "fyi", "spam"]:
                    if p in ans:
                        return p
            except Exception as e:
                logger.error(f"LLM classification error: {e}")
        
        return "fyi"

    async def draft_response(self, email_id: str) -> str:
        target_email = next((e for e in self.emails if e.email_id == email_id), None)
        if not target_email:
            return "Email not found."

        if not await ollama_client.is_available():
            return "LLM not available to draft response."
            
        prompt = f"Draft a professional, concise email response. Match a friendly but professional tone.\n\nOriginal Email:\nFrom: {target_email.from_addr}\nSubject: {target_email.subject}\nBody: {target_email.body}\n\nDraft:"
        try:
            draft = await ollama_client.chat([
                {"role": "system", "content": "You are a helpful assistant drafting emails."},
                {"role": "user", "content": prompt}
            ])
            
            # Guardian check
            verdict = guardian_engine.evaluate(draft)
            if verdict.level >= DisagreementLevel.SAFETY:
                logger.warning(f"Draft rejected by Guardian: {verdict.reasoning}")
                target_email.draft_response = "Draft blocked by Guardian."
                target_email.draft_status = "rejected"
                return target_email.draft_response

            target_email.draft_response = draft
            target_email.draft_status = "drafted"
            return draft
        except Exception as e:
            logger.error(f"Error drafting response: {e}")
            return "Error drafting response."

    def get_inbox(self, priority: Optional[str] = None) -> list[EmailMessage]:
        if priority:
            return [e for e in self.emails if e.priority == priority]
        return self.emails

    def get_drafts(self) -> list[EmailMessage]:
        return [e for e in self.emails if e.draft_response is not None]

    def approve_draft(self, email_id: str) -> dict:
        target = next((e for e in self.emails if e.email_id == email_id), None)
        if not target:
            return {"status": "error", "message": "Email not found"}
        target.draft_status = "approved"
        return {"status": "success", "message": "Draft approved"}

    def reject_draft(self, email_id: str) -> dict:
        target = next((e for e in self.emails if e.email_id == email_id), None)
        if not target:
            return {"status": "error", "message": "Email not found"}
        target.draft_status = "rejected"
        return {"status": "success", "message": "Draft rejected"}

email_agent = EmailAgent()
