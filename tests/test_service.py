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

    # Deactivated until env is in the yml configs
    # async def test_config_getter(self):
    #     config = self.config
    #     service = Service(**config)
    #     self.assertIsInstance(service.config, Service.Config)
    #     self.assertEqual(dict(service.config), config)

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
        logger.debug("TEST: Starting service")
        await service.start()
        logger.debug("TEST: Service started")
        await asyncio.sleep(config["starttime"] + 1)
        logger.debug("TEST: Service should be running")
        self.assertEqual(service.status(), {"sleep all": SubProcess.State.RUNNING})
