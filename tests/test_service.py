import unittest
import asyncio

from src.taskmaster.service import Service, SubProcess
from src.taskmaster.utils.config import Config


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
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_stop(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await service.stop()
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STOPPED})

    async def test_restart(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        asyncio.create_task(service.restart())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_restart_when_not_started_yet(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.01)
        asyncio.create_task(service.restart())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_autorestart_always(self):
        config = self.config
        config["autorestart"] = "always"
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})

    async def test_autorestart_unexpected_should_restart(self):
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})

    async def test_autorestart_unexpected_shouldnt_restart(self):
        config = self.config
        config["autorestart"] = "unexpected"
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.STARTING})

    async def test_autorestart_with_retries(self):
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        config["startretries"] = 2
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(2)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
        await asyncio.sleep(1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.STARTING})

    async def test_autostart(self):
        config = self.config
        config["autostart"] = True
        service = Service(**config)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STOPPED})
        asyncio.create_task(service.autostart())
        await asyncio.sleep(0.1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.STOPPED})
