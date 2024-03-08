import yaml
from .logger import logger
from cerberus import Validator, SchemaError


def validate_dict(data: dict, template: dict) -> bool:
    for key, expected_type in template.items():
        if not len(data) == len(template):
            return "Invalid number of keys."
        if key not in data:
            return key + " is missing."
        if not isinstance(data[key], expected_type):
            return key + " is not of type " + str(expected_type)
    return None


schema = {
    "services": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "required": True,
                    "maxlength": 32,
                    "minlength": 1,
                },
                "cmd": {
                    "type": "string",
                    "required": True,
                },
                "numprocs": {
                    "type": "integer",
                    "min": 1,
                    "max": 32,
                    "required": True,
                },
                "umask": {
                    "type": "integer",
                    "min": 0,
                    "max": 777,
                    "required": True,
                },
                "workingdir": {
                    "type": "string",
                    "required": True,
                },
                "autostart": {
                    "type": "boolean",
                    "required": True,
                },
                "autorestart": {
                    "type": "string",
                    "required": True,
                    "allowed": ["unexpected", "always", "never"],
                },
                "exitcodes": {
                    "type": "list",
                    "required": True,
                    "schema": {"type": "integer", "min": 0, "max": 255},
                },
                "startretries": {
                    "type": "integer",
                    "min": 1,
                    "max": 10,
                    "required": True,
                },
                "starttime": {"type": "integer", "min": 0, "required": True},
                "stopsignal": {
                    "type": "string",
                    "required": True,
                    "allowed": ["TERM", "HUP", "INT", "QUIT", "KILL", "USR1", "USR2"],
                },
                "stoptime": {
                    "type": "integer",
                    "min": 0,
                    "required": True,
                },
                "stdout": {
                    "type": "string",
                },
                "stderr": {
                    "type": "string",
                },
                "user": {
                    "type": "string",
                },
            },
        },
    }
}

validator = Validator(schema)


class Config:
    """
    A class to handle the configuration file for Taskmaster.
    """

    def __init__(self, path="taskmaster.yml"):
        # Try to open if it exists `taskmaster.yml`
        try:
            with open(path, "r") as file:
                content = yaml.safe_load(file)
                if not validator.validate(content):
                    raise SchemaError(validator.errors)
                # Check if duplicate name
                names = [service["name"] for service in content["services"]]
                if len(names) != len(set(names)):
                    raise ValueError("Duplicate service names.")
                self.config = content
        except FileNotFoundError:
            # Throw an error if the file does not exist
            logger.error("No configuration file found.")
            raise FileNotFoundError("No configuration file found.")
        except SchemaError as e:
            print(f"Invalid configuration file: {e}")
            logger.error(f"Invalid configuration file. {e}")
            raise SchemaError("Invalid configuration file.")
        except ValueError as e:
            print(f"Invalid configuration file: {e}")
            logger.error(f"Invalid configuration file. {e}")
            raise ValueError("Invalid configuration file.")
        except Exception:
            logger.error("Failed to read configuration file.")
            raise Exception("Failed to read configuration file.")

    @property
    def services(self):
        return self.config["services"]
