import yaml
from .logger import logger


class Config:
    """
    A class to handle the configuration file for Taskmaster.
    """

    def __init__(self):
        # Try to open if it exists `taskmaster.yml`
        try:
            with open("taskmaster.yml", "r") as file:
                content = yaml.safe_load(file)
                logger.info(content)
        except FileNotFoundError:
            # Throw an error if the file does not exist
            logger.error("No configuration file found.")
            raise FileNotFoundError("No configuration file found.")
        except Exception as e:
            logger.error(f"Failed to read configuration file. {e}")
            raise Exception(f"Failed to read configuration file. {e}")
