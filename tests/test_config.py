import unittest
import os
from src.taskmaster.utils.config import Config
from cerberus import SchemaError


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_valid_taskmaster(self):
        config = Config()

    def test_valid_autorestart_always(self):
        config = Config("./tests/config_templates/valid/autorestart_always.yaml")
        self.assertEqual(config.services[0]["autorestart"], "always")

    def test_valid_autorestart_never(self):
        config = Config("./tests/config_templates/valid/autorestart_never.yaml")
        self.assertEqual(config.services[0]["autorestart"], "never")

    def test_valid_autorestart_unexpected(self):
        config = Config("./tests/config_templates/valid/autorestart_unexpected.yaml")
        self.assertEqual(config.services[0]["autorestart"], "unexpected")

    def test_valid_autostart_false(self):
        config = Config("./tests/config_templates/valid/autostart_false.yaml")
        self.assertEqual(config.services[0]["autostart"], False)

    def test_valid_autostart_true(self):
        config = Config("./tests/config_templates/valid/autostart_true.yaml")
        self.assertEqual(config.services[0]["autostart"], True)

    def test_valid_umask_min(self):
        config = Config("./tests/config_templates/valid/umask_min.yaml")
        self.assertEqual(config.services[0]["umask"], 0)

    def test_valid_umask_max(self):
        config = Config("./tests/config_templates/valid/umask_max.yaml")
        self.assertEqual(config.services[0]["umask"], 777)

    def test_valid_numprocs_min(self):
        config = Config("./tests/config_templates/valid/numprocs_min.yaml")
        self.assertEqual(config.services[0]["numprocs"], 1)

    def test_valid_numprocs_max(self):
        config = Config("./tests/config_templates/valid/numprocs_max.yaml")
        self.assertEqual(config.services[0]["numprocs"], 32)

    def test_valid_starttime_min(self):
        config = Config("./tests/config_templates/valid/starttime_min.yaml")
        self.assertEqual(config.services[0]["starttime"], 0)

    def test_valid_starttime_max(self):
        config = Config("./tests/config_templates/valid/starttime_max.yaml")
        self.assertEqual(config.services[0]["starttime"], 100000000)

    def test_valid_startretries_min(self):
        config = Config("./tests/config_templates/valid/startretries_min.yaml")
        self.assertEqual(config.services[0]["startretries"], 1)

    def test_valid_startretries_max(self):
        config = Config("./tests/config_templates/valid/startretries_max.yaml")
        self.assertEqual(config.services[0]["startretries"], 10)

    def test_valid_exitcodes_min(self):
        config = Config("./tests/config_templates/valid/exitcodes_min.yaml")
        self.assertEqual(config.services[0]["exitcodes"], [0])

    def test_valid_exitcodes_max(self):
        config = Config("./tests/config_templates/valid/exitcodes_max.yaml")
        self.assertEqual(config.services[0]["exitcodes"], [255])

    def test_valid_name_min(self):
        config = Config("./tests/config_templates/valid/name_min.yaml")
        self.assertEqual(config.services[0]["name"], "a")

    def test_valid_name_max(self):
        config = Config("./tests/config_templates/valid/name_max.yaml")
        self.assertEqual(config.services[0]["name"], "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_valid_global(self):
        config = Config("./tests/config_templates/valid/global.yaml")
        self.assertEqual(config.services[0]["umask"], 63)
        self.assertEqual(config.services[0]["numprocs"], 8)
        self.assertEqual(config.services[0]["starttime"], 5)
        self.assertEqual(config.services[0]["startretries"], 3)
        self.assertEqual(config.services[0]["exitcodes"], [0, 2])
        self.assertEqual(config.services[0]["name"], "sleep all")
        self.assertEqual(config.services[0]["autostart"], True)
        self.assertEqual(config.services[0]["autorestart"], "unexpected")

    def test_invalid_keys_auto(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/autorestart.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_cmd(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/cmd.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_workingdir(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/workingdir.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_name(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/name.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_numprocs(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/numprocs.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_autostart(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/autostart.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_umask(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/umask.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_starttime(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/starttime.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_startretries(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/startretries.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_exitcodes(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/exitcodes.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_stoptime(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/stoptime.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_keys_stopsignal(self):
        try:
            config = Config("./tests/config_templates/invalid/keys/stopsignal.yaml")
        except SchemaError as e:
            self.assertIn("Invalid configuration file.", str(e))

    def test_invalid_file(self):
        try:
            config = Config("./test")
        except FileNotFoundError as e:
            self.assertIn("No configuration file found.", str(e))
