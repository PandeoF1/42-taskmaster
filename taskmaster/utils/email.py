from smtplib import SMTP
import threading

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

    async def send(self, subject, message):  # Maybe need to be async
        """
        Send an email
        """
        email_thread = threading.Thread(
            target=self.__send_email, args=(subject, message)
        )
        email_thread.start()

    async def send_start(self, name: str, state: str):
        await self.send(
            f"Taskmaster - {name} - process started",
            f"We inform you that a process has started in the service {name} and is now in the state {state.lower()}.",
        )

    async def send_stop(self, name: str, state: str):
        await self.send(
            f"Taskmaster - {name} - process stopped",
            f"We inform you that a process has stopped in the service {name} and is now in the state {state.lower()}.",
        )

    async def send_exited(self, name: str, state: str):
        await self.send(
            f"Taskmaster - {name} - process exited",
            f"We inform you that a process has exited in the service {name} and is now in the state {state.lower()}.",
        )

    def __send_email(self, subject, message):
        """
        Internal function to send an email
        """
        try:
            if self.config.email:
                with SMTP(self.config.email["smtp_server"], self.config.email["smtp_port"]) as server:
                    server.starttls()
                    server.login(self.config.email["smtp_email"], self.config.email["smtp_password"])
                    msg = f"Subject: {subject}\n\n{message}"
                    logger.info(f"Sending email to {self.config.email['to']}")
                    server.sendmail(self.config.email["smtp_email"], self.config.email["to"], msg)
                    return True
            else:
                logger.warning("No email configuration found")
                return False
        except Exception as e:
            logger.error(f"Error while sending email: {e}")
            return False
