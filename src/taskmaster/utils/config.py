import yaml
from .logger import logger


def validate_dict(data: dict, template: dict) -> bool:
    for key, expected_type in template.items():
        if not len(data) == len(template):
            return 'Invalid number of keys.'
        if key not in data:
            return key + ' is missing.'
        if not isinstance(data[key], expected_type):
            return key + ' is not of type ' + str(expected_type)
    return None


_taskmaster_template = dict()


_taskmaster_template['main'] = {
    "services": list
}

_taskmaster_template['service'] = {
    "name": str,
    "command": str,
    "replicas": int,
    "autostart": bool,
    "restart": str,  # "always", "never", "unexpected"
    "max_restart": int,
    "unexpected_exit_code": list, 
    "started_at": int,
    "force_stop_after": int,
    "stop_signal": str,  # "SIGTERM", "SIGKILL"
    "stop_timeout": int,  # Time before force kill
    "logs": list, # "stdout", "stderr" # If not present they are not logged
    "env": list,
    "working_dir": str,
    "umask": str
}


class Config:
    """
    A class to handle the configuration file for Taskmaster.
    """

    def __init__(self):
        # Try to open if it exists `taskmaster.yml`
        try:
            with open("taskmaster.yml", "r") as file:
                content = yaml.safe_load(file)
                validator = validate_dict(content, _taskmaster_template['main'])
                if validator is not None:
                    logger.error(f"Invalid configuration file. {validator}")
                    raise Exception(validator)
                self.services = content['services']
                for service in self.services:
                    validator = validate_dict(service, _taskmaster_template['service'])
                    if validator is not None:
                        logger.error(f"Invalid configuration file. {validator}")
                        raise Exception(validator)
                self.config = content
        except FileNotFoundError:
            # Throw an error if the file does not exist
            logger.error("No configuration file found.")
            raise FileNotFoundError("No configuration file found.")
        except Exception:
            logger.error(f"Failed to read configuration file.")
            raise Exception(f"Failed to read configuration file.")

    def get_services(self):
        return self.config['services']

    def get_services_keys(self):
        return self.config['services']
