import unittest
import asyncio

from src.taskmaster.service import Service, SubProcess
from src.taskmaster.utils.config import Config
from src.taskmaster.utils.logger import logger


class TestService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = Config(
            "./tests/config_templates/valid/service_reference.yaml"
        ).services[0]

    async def test_config_getter(self):
        config = self.config
        service = Service(**config)
        self.assertIsInstance(service.config, Service.Config)
        self.assertEqual(dict(service.config), config)

    async def test_config_setter(self):
        config = self.config
        service = Service(**config)
        config["cmd"] = "echo 'fake command'"
        service.config = config
        self.assertEqual(
            dict(service.config),
            dict(Service.Config(**config)),
        )

    async def test_start(self):
        config = self.config
        service = Service(**config)
        task = asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await task
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_stop(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await service.stop()
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STOPPED})

    async def test_restart(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        task = asyncio.create_task(service.restart())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await task
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_restart_when_not_started_yet(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        task = asyncio.create_task(service.restart())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await task
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_autorestart_always(self):
        config = self.config
        config["autorestart"] = "always"
        print(config)
        service = Service(**config)
        asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        while service.status.get("sleep all") == SubProcess.State.RUNNING:
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_autorestart_unexpected(self):
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        service = Service(**config)
        asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        while service.status.get("sleep all") == SubProcess.State.RUNNING:
            await asyncio.sleep(0.1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_autorestart_with_retries(self):
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        config["startretries"] = 2
        service = Service(**config)
        asyncio.create_task(service.start())
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        while service.status.get("sleep all") == SubProcess.State.RUNNING:
            await asyncio.sleep(0.1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        self.assertEqual(service._processes[0]._retries, 1)
        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status.get("sleep all") == SubProcess.State.RUNNING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)

        self.assertEqual(service._processes[0]._retries, 2)

        while (
            service.status.get("sleep all") == SubProcess.State.STOPPED
            or service.status.get("sleep all") == SubProcess.State.STARTING
            or service.status.get("sleep all") == SubProcess.State.RUNNING
            or service.status == {}
        ):
            await asyncio.sleep(0.1)

        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
