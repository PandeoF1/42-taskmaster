import yaml
from .logger import logger
from cerberus import Validator, SchemaError

keys = [
    "name",
    "cmd",
    "numprocs",
    "umask",
    "workingdir",
    "autostart",
    "autorestart",
    "exitcodes",
    "startretries",
    "starttime",
    "stopsignal",
    "stoptime",
    "stdout",
    "stderr",
    "user",
]

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
                # Sort keys to have all services in the same order
                data = content["services"]
                _services = []
                for service in data:
                    # For each optionnal key if don't exist add it
                    service.setdefault("stdout", "")
                    service.setdefault("stderr", "")
                    service.setdefault("user", "")
                    # range key in this order : name, cmd, numprocs, umask, workingdir, autostart, autorestart, exitcodes, startretries, starttime, stopsignal, stoptime, stdout, stderr, user
                    _service = dict()
                    for key in keys:
                        _service[key] = service[key]
                    _services.append(_service)
                    # sorted(_service.items(), key=lambda x: x[0])

                content["services"] = [dict(service) for service in _services]
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
        except Exception as e:
            logger.error(f"Failed to read configuration file. {e}")
            raise Exception("Failed to read configuration file.")

    @property
    def services(self):
        return self.config["services"]
