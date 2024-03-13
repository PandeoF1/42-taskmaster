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

    # async def test_config_setter(self):
    #     config = self.config
    #     service = Service(**config)
    #     config["cmd"] = "echo 'fake command'"
    #     service.config = config
    #     self.assertEqual(
    #         dict(service.config),
    #         dict(Service.Config(**config)),
    #     )

    async def test_start(self):
        config = self.config
        service = Service(**config)
        logger.debug("TESTS: Starting task")
        task = asyncio.create_task(service.start())
        logger.debug("TESTS: Task started")
        logger.debug("TESTS: Looping to check if the service is running")
        while (
            service.status().get("sleep all") == SubProcess.State.STOPPED
            or service.status().get("sleep all") == SubProcess.State.STARTING
            or service.status() == {}
        ):
            logger.debug("TESTS: sleep")
            await asyncio.sleep(0.1)
        logger.debug("TESTS: Loop done")
        self.assertEqual(service.status(), {"sleep all": SubProcess.State.RUNNING})
        logger.debug("TESTS: Waiting for task to finish")
        await task
        logger.debug("TESTS: Task finished")
        self.assertEqual(service.status(), {"sleep all": SubProcess.State.EXITED})
