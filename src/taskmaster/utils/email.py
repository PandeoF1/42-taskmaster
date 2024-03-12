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
            if "email" in self.config.config:
                server = smtplib.SMTP(
                    self.config["smtp_server"], self.config["smtp_port"]
                )
                server.starttls()
                server.login(self.config["smtp_email"], self.config["smtp_password"])
                msg = f"Subject: {subject}\n\n{message}"
                server.sendmail(self.config["smtp_email"], self.config["to"], msg)
                server.quit()
                return True
            else:
                logger.warning("No email configuration found")
                return False
        except Exception as e:
            logger.error(f"Error while sending email: {e}")
            return False
