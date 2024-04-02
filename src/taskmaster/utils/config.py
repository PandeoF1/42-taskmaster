import yaml
from .logger import logger
from cerberus import Validator, SchemaError
from enum import Enum

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
    "env",
    "stdout",
    "stderr",
    "user",
]


class AutoRestart(Enum):
    """
    Enumeration for auto restart options.

    Options:
    - ALWAYS: Always restart the service.
    - NEVER: Never restart the service.
    - UNEXPECTED: Restart the service only if it terminates unexpectedly.
    """

    ALWAYS = "always"
    NEVER = "never"
    UNEXPECTED = "unexpected"


class Signal(Enum):
    """
    Enumeration for signals.

    Options:
    - USR1: User-defined signal 1.
    - USR2: User-defined signal 2.
    - INT: Interrupt signal.
    - TERM: Terminate signal.
    - HUP: Hangup signal.
    - QUIT: Quit signal.
    """

    USR1 = 10
    USR2 = 12
    INT = 2
    TERM = 15
    HUP = 1
    QUIT = 3


schema = {
    "email": {
        "type": "dict",
        "schema": {
            "smtp_server": {
                "type": "string",
                "required": True,
                "minlength": 1,
            },
            "smtp_port": {
                "type": "integer",
                "required": True,
            },
            "smtp_email": {
                "type": "string",
                "required": True,
                "minlength": 1,
                "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            },
            "smtp_password": {
                "type": "string",
                "required": True,
            },
            "to": {
                "type": "string",
                "required": True,
                "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
            },
        },
    },
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
                    "allowed": [e.value for e in AutoRestart],
                },
                "exitcodes": {
                    "type": "list",
                    "required": True,
                    "schema": {"type": "integer", "min": 0, "max": 255},
                },
                "startretries": {
                    "type": "integer",
                    "min": 0,
                    "max": 10,
                    "required": True,
                },
                "starttime": {"type": "integer", "min": 0, "required": True},
                "stopsignal": {
                    "type": "string",
                    "required": True,
                    "allowed": [e.name for e in Signal],
                },
                "stoptime": {
                    "type": "integer",
                    "min": 0,
                    "required": True,
                },
                "env": {
                    "type": "dict",
                },
                "stdout": {
                    "type": "string",
                    "minlength": 1,
                },
                "stderr": {
                    "type": "string",
                    "minlength": 1,
                },
                "user": {
                    "type": "string",
                    "minlength": 1,
                },
            },
        },
    },
}

validator = Validator(schema)


class Config:
    """
    A class to handle the configuration file for Taskmaster.
    """

    def __init__(self, path="taskmaster.yml"):
        # Try to open if it exists `taskmaster.yml`
        try:
            self.path = path
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
                    service.setdefault("stdout", None)
                    service.setdefault("stderr", None)
                    service.setdefault("user", None)
                    service.setdefault("env", {})
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
            logger.error(f"Invalid configuration file. {e}")
            raise SchemaError("Invalid configuration file.")
        except ValueError as e:
            logger.error(f"Invalid configuration file. {e}")
            raise ValueError("Invalid configuration file.")
        except Exception as e:
            logger.error(f"Failed to read configuration file. {e}")
            raise Exception("Failed to read configuration file.")

    @property
    def services(self):
        return self.config["services"]

    @property
    def email(self):
        if "email" not in self.config:
            return None
        return self.config["email"]


def generate_config(path: str):
    """
    Generate a default configuration file.

    Args:
    - path: The path to the configuration file.
    """

    try:
        with open(path, "w") as file:
            file.write(
                """\
email:
  to: ""
  smtp_email: ""
  smtp_password: ""
  smtp_server: "smtp.gmail.com"
  smtp_port: 465

services:
  - name:
    cmd:
    numprocs: 1 # min 1 max 32
    umask: 077
    workingdir: /tmp
    autostart: true
    autorestart: unexpected # always, never unexpected
    exitcodes:
    - 0
    startretries: 3
    starttime: 5
    stopsignal: USR1
    stoptime: 10
    # env:
    #  key: "value"
    # stdout: /tmp/taskmaster.log
    # stderr: /tmp/taskmaster.log
    # user: xxx
"""
            )
    except Exception as e:
        logger.error(f"Failed to generate configuration file. {e}")
        raise Exception("Failed to generate configuration file.")
