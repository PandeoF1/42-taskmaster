import logging
import os

class logger:
    """
    A class that creates a file logger and directs logs to a file.

    Attributes:
        logger_name (str): The name of the logger.
        log_file (str): The path to the log file.
    """

    def __init__(self, logger_name: str, log_dir: str = "logs") -> None:
        """
        Initializes the Logger object.

        Args:
            logger_name (str): The name of the logger (e.g., "my_app", "db_access").
            log_dir (str, optional): The directory to store the log file. Defaults to "logs".
        """

        self.logger_name = logger_name
        self.log_file = os.path.join(log_dir, f"{logger_name}.log")

        # Ensure the log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Create the logger instance
        self.logger = logging.getLogger(self.logger_name)

        # Create a file handler
        file_handler = logging.FileHandler(self.log_file)

        # Set a formatter for the log messages
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(file_handler)

        # Set the logging level (optional)
        self.logger.setLevel(logging.INFO)  # You can adjust the level as needed

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Logs a message to the file.

        Args:
            message (str): The message to log.
            level (str, optional): The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). Defaults to "INFO".
        """

        level_method = getattr(self.logger, level.lower())  # Get the appropriate logging method
        level_method(message)

    def close(self) -> None:
        """
        Closes the file handler associated with the logger.
        """

        for handler in self.logger.handlers:
            handler.close()
