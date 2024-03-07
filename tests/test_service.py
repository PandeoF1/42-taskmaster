import unittest
from unittest.mock import MagicMock
from src.taskmaster.service import Service, ServiceConfig


class TestService(unittest.TestCase):
    def setUp(self) -> None:
        self.service_config: dict = {
            "services": [
                {
                    "name": "program1",
                    "command": "echo 'Hello, World!'",
                    "autostart": True,
                    "autorestart": "unexpected",
                    "exitcodes": [0],
                    "startretries": 3,
                    "starttime": 1,
                    "stoptime": 1,
                    "stdout": "stdout.log",
                    "stderr": "stderr.log",
                },
                {
                    "name": "program2",
                    "command": "echo 'Hello, World!'",
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
        self.service = Service(**self.service_config)

    # def test_start_all_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.start()
    #     program1.start.assert_called_once()
    #     program2.start.assert_called_once()

    # def test_start_specific_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.start(program_names=["program1"])
    #     program1.start.assert_called_once()
    #     program2.start.assert_not_called()

    # def test_stop_all_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.stop()
    #     program1.stop.assert_called_once()
    #     program2.stop.assert_called_once()

    # def test_stop_specific_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.stop(program_names=["program1"])
    #     program1.stop.assert_called_once()
    #     program2.stop.assert_not_called()

    # def test_restart_all_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.restart()
    #     program1.restart.assert_called_once()
    #     program2.restart.assert_called_once()

    # def test_restart_specific_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.restart(program_names=["program1"])
    #     program1.restart.assert_called_once()
    #     program2.restart.assert_not_called()

    def test_config_getter(self):
        config = self.service.config
        self.assertIsInstance(config, ServiceConfig)

    def test_config_setter(self):
        config = {"key": "value"}
        self.service.config = config
        self.assertEqual(dict(self.service.config), dict(ServiceConfig(**config)))

    # def test_reload_all_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.reload()
    #     program1.reload.assert_called_once()
    #     program2.reload.assert_called_once()

    # def test_reload_specific_programs(self):
    #     program1 = MagicMock()
    #     program2 = MagicMock()
    #     self.service._programs = [program1, program2]
    #     self.service.reload(program_names=["program1"])
    #     program1.reload.assert_called_once()
    #     program2.reload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
