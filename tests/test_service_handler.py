import unittest
import asyncio
from typing import Any, Dict

from src.taskmaster.service import ServiceHandler
from src.taskmaster.utils.config import Config


class TestServiceHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = Config("./tests/config_templates/valid/service_handler_reference.yaml")
        self.config: Dict[str, Dict[str, Any]] = dict({"services": config.services})

    async def test_config_getter(self):
        config = self.config
        service_handler = ServiceHandler(**config)
        self.assertIsInstance(service_handler.config, ServiceHandler.Config)
        self.assertEqual(dict(service_handler.config), config)

    async def test_config_setter(self):
        config = self.config
        service = ServiceHandler(**config)
        services = config.get("services")
        services[0]["cmd"] = "echo 'fake command'"  # type: ignore
        service.config = config
        self.assertEqual(
            dict(service.config),
            dict(ServiceHandler.Config(**config)),
        )

    async def test_start(self):
        config = self.config
        config["services"][0]["autostart"] = False  # type: ignore
        service = ServiceHandler(**config)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Stopped",
                    "process_2": "Stopped",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Stopped",
                    "process_2": "Stopped",
                    "process_3": "Stopped",
                },
            ],
        )
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Starting",
                    "process_2": "Starting",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )
        await asyncio.sleep(1)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Running",
                    "process_2": "Running",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )
        await asyncio.sleep(1)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Exited",
                    "process_2": "Exited",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )

    async def test_stop_when_starting(self):
        config = self.config
        config["services"][0]["autostart"] = False  # type: ignore
        service = ServiceHandler(**config)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Stopped",
                    "process_2": "Stopped",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Stopped",
                    "process_2": "Stopped",
                    "process_3": "Stopped",
                },
            ],
        )
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Starting",
                    "process_2": "Starting",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )
        asyncio.create_task(service.stop())
        await asyncio.sleep(0.001)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Stopping",
                    "process_2": "Stopping",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )
        await asyncio.sleep(1)
        self.assertEqual(
            service.status(),
            [
                {
                    "name": "sleep all",
                    "cmd": "sleep 2",
                    "process_1": "Stopped",
                    "process_2": "Stopped",
                },
                {
                    "name": "echo OUIII",
                    "cmd": "echo OUIII",
                    "process_1": "Exited",
                    "process_2": "Exited",
                    "process_3": "Exited",
                },
            ],
        )

    async def test_start_after_all_processes_exited(self):
        config = self.config
        config["services"][0]["autorestart"] = "always"  # type: ignore
        config["services"][0]["startretries"] = 1  # type: ignore
        service = ServiceHandler(**config)
        asyncio.create_task(service.autostart())
        await asyncio.sleep(5.1)
        print(service.status())
        self.assertEqual(
            service.status()[0],
            {
                "name": "sleep all",
                "cmd": "sleep 2",
                "process_1": "Fatal",
                "process_2": "Fatal",
            },
        )
        asyncio.create_task(service.start(["sleep all"]))
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status()[0],
            {
                "name": "sleep all",
                "cmd": "sleep 2",
                "process_1": "Starting",
                "process_2": "Starting",
            },
        )
        await asyncio.sleep(3.0)
        self.assertEqual(
            service.status()[0],
            {
                "name": "sleep all",
                "cmd": "sleep 2",
                "process_1": "Starting",
                "process_2": "Starting",
            },
        )

    async def test_restart(self):
        pass

    async def test_autostart(self):
        pass

    async def test_reload(self):
        pass
