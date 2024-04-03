import unittest
import asyncio
from typing import Any, Dict

from taskmaster.service import ServiceHandler
from taskmaster.utils.config import Config


class TestServiceHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = Config("./tests/config_templates/valid/service_handler_reference.yaml")
        self.config: Dict[str, Dict[str, Any]] = dict({"services": config.services})

    async def test_config_getter(self):
        self.maxDiff = None
        config = self.config
        service_handler = ServiceHandler(email=None, **config)
        self.assertIsInstance(service_handler.config, ServiceHandler.Config)
        self.assertEqual(dict(service_handler.config), config)

    async def test_config_setter(self):
        config = self.config
        service = ServiceHandler(email=None, **config)
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
        service = ServiceHandler(email=None, **config)
        self.assertEqual(
            service.status,
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
            service.status,
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
            service.status,
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
            service.status,
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
        service = ServiceHandler(email=None, **config)
        self.assertEqual(
            service.status,
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
            service.status,
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
            service.status,
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
            service.status,
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
        service = ServiceHandler(email=None, **config)
        asyncio.create_task(service.autostart())
        await asyncio.sleep(5.1)
        self.assertEqual(
            service.status[0],
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
            service.status[0],
            {
                "name": "sleep all",
                "cmd": "sleep 2",
                "process_1": "Starting",
                "process_2": "Starting",
            },
        )
        await asyncio.sleep(3.0)
        self.assertEqual(
            service.status[0],
            {
                "name": "sleep all",
                "cmd": "sleep 2",
                "process_1": "Starting",
                "process_2": "Starting",
            },
        )

    async def test_reload_new_service(self):
        config = self.config
        handler = ServiceHandler(email=None, **config)
        asyncio.create_task(handler.start())
        await asyncio.sleep(1)
        config["services"].append(
            {
                "name": "blabla",
                "cmd": "echo blabla",
                "autostart": False,
                "autorestart": "always",
                "startretries": 1,
                "stdout": "/tmp/sleep.stdout",
                "stderr": "/tmp/sleep.stderr",
                "numprocs": 1,
                "exitcodes": [0, 2],
                "stopsignal": "SIGTERM",
                "stopwaitsecs": 10,
                "umask": "022",
                "workingdir": "/tmp",
                "env": {"OUI": "OUI"},
                "user": None,
            }
        )
        handler.config = config
        asyncio.create_task(handler.reload())
        await asyncio.sleep(0.1)
        self.assertEqual(
            handler.status[2],
            {
                "name": "blabla",
                "cmd": "echo blabla",
                "process_1": "Stopped",
            },
        )
        self.assertEqual(
            handler.status[1],
            {
                "name": "echo OUIII",
                "cmd": "echo OUIII",
                "process_1": "Exited",
                "process_2": "Exited",
                "process_3": "Exited",
            },
        )

    async def test_reload_remove_service(self):
        config = self.config
        handler = ServiceHandler(email=None, **config)
        asyncio.create_task(handler.start())
        await asyncio.sleep(1)
        config["services"].pop(0)
        handler.config = config
        asyncio.create_task(handler.reload())
        await asyncio.sleep(0.1)
        self.assertEqual(
            handler.status[0],
            {
                "name": "echo OUIII",
                "cmd": "echo OUIII",
                "process_1": "Exited",
                "process_2": "Exited",
                "process_3": "Exited",
            },
        )
        self.assertEqual(len(handler.status), 1)

    async def test_reload_update_service(self):
        config = self.config
        handler = ServiceHandler(email=None, **config)
        asyncio.create_task(handler.start())
        await asyncio.sleep(1)
        config["services"][0]["cmd"] = "echo 'fake command'"
        handler.config = config
        asyncio.create_task(handler.reload())
        await asyncio.sleep(0.1)
        self.assertEqual(
            handler.status[0],
            {
                "name": "sleep all",
                "cmd": "echo 'fake command'",
                # Autostart is True
                "process_1": "Starting",
                "process_2": "Starting",
            },
        )
        self.assertEqual(
            handler.status[1],
            {
                "name": "echo OUIII",
                "cmd": "echo OUIII",
                "process_1": "Exited",
                "process_2": "Exited",
                "process_3": "Exited",
            },
        )

    async def test_reload_update_service_with_autostart_false(self):
        config = self.config
        handler = ServiceHandler(email=None, **config)
        asyncio.create_task(handler.start())
        await asyncio.sleep(1)
        config["services"][0]["cmd"] = "echo 'fake command'"
        config["services"][0]["autostart"] = False
        handler.config = config
        asyncio.create_task(handler.reload())
        await asyncio.sleep(0.1)
        self.assertEqual(
            handler.status[0],
            {
                "name": "sleep all",
                "cmd": "echo 'fake command'",
                "process_1": "Stopped",
                "process_2": "Stopped",
            },
        )
        self.assertEqual(
            handler.status[1],
            {
                "name": "echo OUIII",
                "cmd": "echo OUIII",
                "process_1": "Exited",
                "process_2": "Exited",
                "process_3": "Exited",
            },
        )

    async def test_delete(self):
        config = self.config
        handler = ServiceHandler(email=None, **config)
        asyncio.create_task(handler.start())
        await asyncio.sleep(1)
        await handler.delete()
        self.assertEqual(handler.status, [])
