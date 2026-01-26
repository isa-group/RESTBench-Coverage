# email_sender.py
import logging
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

CURRENT_DIR = Path(__file__).parent.resolve()
ENV = CURRENT_DIR / ".env"

# Auto-load .env (if python-dotenv is installed)
# try:
#     from dotenv import load_dotenv
#
#     load_dotenv(dotenv_path=ENV)  # Default: search for .env in project root or current directory
#
#     # Check if key variables are loaded
#     required = ["SENDER_EMAIL", "SENDER_AUTH", "RECIPIENT_EMAIL"]
#     missing = [k for k in required if not os.getenv(k)]
#     if missing:
#         print(f"[email_sender] .env loading failed, missing variables: {', '.join(missing)}")
#     else:
#         print("[email_sender] .env loaded successfully!")
#         print("  SENDER_EMAIL =", os.getenv("SENDER_EMAIL"))
#         print("  RECIPIENT_EMAIL =", os.getenv("RECIPIENT_EMAIL"))
#
# except ImportError:
#     print("[email_sender] python-dotenv not installed, skipping .env loading")

logger = logging.getLogger(__name__)


def _normalize_recipients(recipients: Optional[Union[str, Sequence[str]]]) -> List[str]:
    if recipients is None:
        return []
    if isinstance(recipients, str):
        return [x.strip() for x in recipients.split(",") if x.strip()]
    result: List[str] = []
    for r in recipients:
        if r:
            result.extend(_normalize_recipients(r))
    seen = set()
    uniq: List[str] = []
    for x in result:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


class EmailSender:
    """
    Lightweight email helper for programmatic use.
    Defaults: only send on failure.
    Env fallbacks (can be provided via .env):
      SMTP_HOST, SMTP_PORT, SENDER_EMAIL, SENDER_AUTH, RECIPIENT_EMAIL
    """

    def __init__(
            self,
            enabled: bool = True,
            *,
            on_failure: bool = True,
            on_start: bool = False,
            on_results: bool = False,
            smtp_host: Optional[str] = None,
            smtp_port: Optional[int] = None,
            sender_email: Optional[str] = None,
            sender_auth: Optional[str] = None,
            recipients: Optional[Union[str, Sequence[str]]] = None,
            attachment_root: Optional[Union[str, Path]] = None,
            timeout_sec: int = 10,
    ):
        self.enabled = enabled
        self.on_failure = on_failure
        self.on_start = on_start
        self.on_results = on_results

        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.exmail.qq.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "465"))

        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "")
        self.sender_auth = sender_auth or os.getenv("SENDER_AUTH", "")
        env_rcpts = os.getenv("RECIPIENT_EMAIL", "")
        self._recipients: List[str] = _normalize_recipients(recipients) or _normalize_recipients(env_rcpts)

        self.attachment_root = Path(attachment_root) if attachment_root else Path.cwd()
        self.timeout_sec = timeout_sec

        if not self.enabled:
            logger.info("EmailSender: disabled (no emails will be sent).")

    # ----------------- public helpers -----------------

    def set_recipients(self, recipients: Union[str, Sequence[str]]) -> None:
        self._recipients = _normalize_recipients(recipients)

    def add_recipient(self, recipient: str) -> None:
        r = _normalize_recipients(recipient)
        for x in r:
            if x not in self._recipients:
                self._recipients.append(x)

    def get_recipients(self) -> List[str]:
        return list(self._recipients)

    # ----------------- core send -----------------

    def send_message(
            self,
            subject: str,
            body: str,
            *,
            attachments: Optional[Iterable[Union[str, Path]]] = None,
            to: Optional[Union[str, Sequence[str]]] = None,
    ) -> bool:
        if not self.enabled:
            logger.debug("send_message skipped: EmailSender disabled.")
            return False

        recipients = _normalize_recipients(to) or self._recipients
        if not recipients:
            logger.warning("send_message skipped: no recipients.")
            return False

        if not self.sender_email or not self.sender_auth:
            logger.error("send_message skipped: missing SENDER_EMAIL/SENDER_AUTH.")
            return False

        msg = EmailMessage()
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)

        if attachments:
            for att in attachments:
                self._attach_file(msg, att)

        try:
            with smtplib.SMTP_SSL(host=self.smtp_host, port=self.smtp_port, timeout=self.timeout_sec) as server:
                server.login(self.sender_email, self.sender_auth)
                server.send_message(msg)
                logger.info("Email sent: %s -> %s", subject, recipients)
                return True
        except Exception as e:
            logger.error("Email send failed: %s", e)
            return False

    # ----------------- convenience wrappers -----------------

    def send_results(self, subj: str) -> None:
        if not (self.enabled and self.on_results):
            logger.debug("send_results skipped.")
            return
        self.send_message(
            subject=f"Test Reports for {subj}",
            body="Hello,\n\nAttached are summary.csv and pit-reports.txt.\n\nBest,\nAutomated Test System",
            attachments=["summary.csv", "pit-reports.txt"],
        )

    def send_notification(self, api: str, operation: str, mode: str, level: str, strength: str) -> None:
        if not (self.enabled and self.on_start):
            logger.debug("send_notification skipped.")
            return
        self.send_message(
            subject=f"[{api}-{operation}] Experiment Started",
            body=(
                f"Hello,\n\nExperiment started with:\n"
                f"  API: {api}\n  Operation: {operation}\n"
                f"  Mode: {mode}\n  Level: {level}\n  Strength: {strength}\n\n"
                f"Best,\nAutomated Test System"
            ),
        )

    def send_failure_email(self, command: str, error_output: str) -> None:
        if not (self.enabled and self.on_failure):
            logger.debug("send_failure_email skipped.")
            return
        self.send_message(
            subject="Command Failure Notification",
            body=(
                f"Hello,\n\nThe following command failed:\n\n"
                f"    {command}\n\nCaptured output:\n\n{error_output}\n\n"
                f"Please check logs.\n\nBest,\nAutomated Test System"
            ),
        )

    # ----------------- internals -----------------

    def _attach_file(self, msg: EmailMessage, path: Union[str, Path]) -> None:
        p = Path(path)
        if not p.is_absolute():
            p = self.attachment_root / p
        if not p.exists():
            logger.warning("Attachment not found: %s", p)
            return
        mime_type, _ = mimetypes.guess_type(str(p))
        if not mime_type:
            mime_type = "application/octet-stream"
        maintype, subtype = mime_type.split("/", 1)
        with open(p, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=p.name)


if __name__ == "__main__":
    from pathlib import Path
    import tempfile

    print("[email_sender] Sending real test emails... (check your inbox)")

    # Construct an EmailSender with all features enabled
    sender = EmailSender(enabled=True, on_failure=True, on_start=True, on_results=True)

    # 1. Test failure email
    sender.send_failure_email("echo FAIL", "This is a simulated failure output.")

    # 2. Test start notification
    sender.send_notification("TestAPI", "postUsers", "WHITE", "OAS", "ONE_WAY")

    # 3. Create temporary attachment files for testing results email
    tmpdir = Path(tempfile.gettempdir())
    (tmpdir / "summary.csv").write_text("id,value\n1,42\n", encoding="utf-8")
    (tmpdir / "pit-reports.txt").write_text("dummy pit content", encoding="utf-8")

    # 4. Test results email (with attachments)
    sender.attachment_root = tmpdir
    sender.send_results("Manual Test Batch")

    # 5. Test generic interface
    (tmpdir / "custom.log").write_text("hello world", encoding="utf-8")
    sender.send_message(
        subject="Custom Notice",
        body="Hi there, this is a custom message with attachment.",
        attachments=["custom.log"]
    )

    print("[email_sender] Done. Check your mailbox for 4 test emails.")
