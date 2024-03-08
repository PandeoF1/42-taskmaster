import unittest

# from unittest.mock import MagicMock
from src.taskmaster.service import ServiceHandler, ServiceHandlerConfig


class TestService(unittest.TestCase):
    def setUp(self) -> None:
        self.service_config: dict = {
            "services": [
                {
                    "name": "program1",
                    "cmd": "echo 'This is program 1'",
                    "numprocs": 1,
                    "umask": 0o77,
                    "workingdir": "/tmp",
                    "autostart": True,
                    "autorestart": "unexpected",
                    "exitcodes": [0, 2],
                    "startretries": 3,
                    "starttime": 1,
                    "stoptime": 1,
                    "stdout": "stdout.log",
                    "stderr": "stderr.log",
                },
                {
                    "name": "program2",
                    "cmd": "echo 'This is program 2'",
                    "numprocs": 1,
                    "umask": 0o77,
                    "workingdir": "/tmp",
                    "autostart": True,
                    "autorestart": "unexpected",
                    "exitcodes": [0],
                    "startretries": 3,
                    "starttime": 1,
                    "stoptime": 1,
                    "stdout": "stdout.log",
                    "stderr": "stderr.log",
                },
            ],
        }
        self.service = ServiceHandler(**self.service_config)

    def test_config_getter(self):
        config = self.service.config
        self.assertIsInstance(config, ServiceHandlerConfig)
        self.assertEqual(dict(config), self.service_config)

    def test_config_setter(self):
        self.service_config["services"][0]["cmd"] = "echo 'fake command'"
        self.service.config = self.service_config
        self.assertEqual(
            dict(self.service.config), dict(ServiceHandlerConfig(**self.service_config))
        )

    def test_start(self):
        pass


if __name__ == "__main__":
    unittest.main()
