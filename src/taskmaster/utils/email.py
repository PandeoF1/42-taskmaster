import smtplib
from .logger import logger


class Email:
    """
    This class permit to send email
    """

    def __init__(self, config):
        """
        Constructor of Email class
        """
        self.config = config

    def send(self, subject, message):  # Maybe need to be async
        """
        Send an email
        """
        try:
            if self.config.email:
                server = smtplib.SMTP(
                    self.config.email["smtp_server"], self.config.email["smtp_port"]
                )
                server.starttls()
                server.login(
                    self.config.email["smtp_email"], self.config.email["smtp_password"]
                )
                msg = f"Subject: {subject}\n\n{message}"
                server.sendmail(
                    self.config.email["smtp_email"], self.config.email["to"], msg
                )
                server.quit()
                return True
            else:
                logger.warning("No email configuration found")
                return False
        except Exception as e:
            logger.error(f"Error while sending email: {e}")
            return False
