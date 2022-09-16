import smtplib
import time

from dataclasses import dataclass
from email.message import EmailMessage
from typing import List

from humanfriendly import format_timespan


@dataclass
class EmailConfig:
    smtp_server_address: str
    smtp_server_port: int
    sender_email_address: str
    sender_email_password: str
    recipients: List[str]


def send_email(config: EmailConfig, url: str):
    msg = EmailMessage()
    msg.set_content(f"Product now in stock at {url}")

    msg["Subject"] = "Your product is now in stock"
    msg["From"] = config.sender_email_address
    msg["To"] = config.recipients

    mail_server = smtplib.SMTP(config.smtp_server_address, config.smtp_server_port)
    mail_server.ehlo()
    mail_server.starttls()
    mail_server.ehlo()
    mail_server.login(config.sender_email_address, config.sender_email_password)
    mail_server.sendmail(
        config.sender_email_address,
        config.recipients,
        msg.as_string(),
    )
    mail_server.quit()


def wait_until_next_iteration(interval: int) -> None:
    remaining_seconds = interval
    print("")
    while remaining_seconds > 0:
        print(f"\rNext check in {format_timespan(remaining_seconds)}...\033[K", end="")
        time.sleep(1)
        remaining_seconds -= 1
    print("\r\033[K", end="")
