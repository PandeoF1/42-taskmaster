import yaml


class Config:
    """
    A class to handle the configuration file for Taskmaster.
    """

    def __init__(self):
        # Try to open if it exists `taskmaster.yml`
        try:
            with open("taskmaster.yml", "r") as file:
                content = yaml.safe_load(file)
                print(content)
        except FileNotFoundError:
            # log.log("No configuration file found.")
            return None
        except Exception as e:
            # log.log("Failed to read configuration file.", level="ERROR")
            return None
