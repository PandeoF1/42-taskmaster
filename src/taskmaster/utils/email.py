from smtplib import SMTP
from .logger import logger
import threading


class Email:
    """
    This class permit to send email
    """

    def __init__(self, config):
        """
        Constructor of Email class
        """
        self.config = config

    async def send(self, subject, message):  # Maybe need to be async
        """
        Send an email
        """
        email_thread = threading.Thread(
            target=send_email, args=(self.config, subject, message)
        )
        email_thread.start()


def send_email(config, subject, message):
    """
    Send an email
    """
    try:
        if config.email:
            with SMTP(config.email["smtp_server"], config.email["smtp_port"]) as server:
                server.starttls()
                server.login(config.email["smtp_email"], config.email["smtp_password"])
                msg = f"Subject: {subject}\n\n{message}"
                server.sendmail(config.email["smtp_email"], config.email["to"], msg)
                return True
        else:
            logger.warning("No email configuration found")
            return False
    except Exception as e:
        logger.error(f"Error while sending email: {e}")
        return False
