import unittest
import asyncio
import pytest
from src.taskmaster.service import Service, SubProcess
from src.taskmaster.utils.config import Config
import os
import subprocess


class TestService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = Config(
            "./tests/config_templates/valid/service_reference.yaml"
        ).services[0]
        # execute make in ./programs/
        subprocess.run(["make"], cwd="./tests/programs/")

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

    async def test_start_async(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})

    async def test_start_await(self):
        config = self.config
        service = Service(**config)
        await service.start()
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})

    async def test_stop_async(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
        asyncio.create_task(service.stop())
        await asyncio.sleep(1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STOPPED})

    async def test_stop_await(self):
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

    async def test_autorestart_with_2_retries(self):
        retries = 2
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        config["startretries"] = retries
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        for i in range(retries + 1):
            self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
            await asyncio.sleep(1)
            self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
            await asyncio.sleep(1)
            if i == retries:
                break
            self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
            await asyncio.sleep(i + 1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.FATAL})

    async def test_autorestart_with_5_retries(self):
        retries = 5
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        config["startretries"] = retries
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        for i in range(retries + 1):
            self.assertEqual(service.status, {"sleep all": SubProcess.State.STARTING})
            await asyncio.sleep(1)
            self.assertEqual(service.status, {"sleep all": SubProcess.State.RUNNING})
            await asyncio.sleep(1)
            if i == retries:
                break
            self.assertEqual(service.status, {"sleep all": SubProcess.State.EXITED})
            await asyncio.sleep(i + 1)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.FATAL})

    async def test_autostart(self):
        config = self.config
        config["autostart"] = True
        service = Service(**config)
        self.assertEqual(service.status, {"sleep all": SubProcess.State.STOPPED})
        asyncio.create_task(service.autostart())
        await asyncio.sleep(0.1)
        self.assertNotEqual(service.status, {"sleep all": SubProcess.State.STOPPED})

    async def test_umask_003(self):
        config = Config("./tests/config_templates/valid/umask03.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"umask 03": SubProcess.State.EXITED})
        with open("/tmp/umask003.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 03\n")

    async def test_umask_077(self):
        config = Config("./tests/config_templates/valid/umask077.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"umask 077": SubProcess.State.EXITED})
        with open("/tmp/umask077.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 077\n")

    async def test_umask_007(self):
        config = Config("./tests/config_templates/valid/umask07.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"umask 07": SubProcess.State.EXITED})
        with open("/tmp/umask007.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 07\n")

    async def test_stdout(self):
        config = Config("./tests/config_templates/valid/stdout.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"stdout": SubProcess.State.EXITED})
        with open("/tmp/stdout.stdout") as f:
            self.assertTrue("---- stdout test ----" in f.read())

    async def test_stderr(self):
        config = Config("./tests/config_templates/valid/stderr.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"stderr": SubProcess.State.EXITED})
        with open("/tmp/stderr.stderr") as f:
            self.assertTrue("---- stderr test ----" in f.read())

    async def test_stdout_no_file(self):
        os.remove("/tmp/stdout.stdout")
        config = Config("./tests/config_templates/valid/stdout_no_file.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"stdout no file": SubProcess.State.EXITED})
        with pytest.raises(FileNotFoundError):
            with open("/tmp/stdout.stdout") as f:
                f.read()
        self.assertTrue(True)

    async def test_stderr_no_file(self):
        os.remove("/tmp/stderr.stderr")
        config = Config("./tests/config_templates/valid/stderr_no_file.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status, {"stderr no file": SubProcess.State.EXITED})
        with pytest.raises(FileNotFoundError):
            with open("/tmp/stderr.stderr") as f:
                f.read()
        self.assertTrue(True)

    # Random tests dont make any sense
    # async def test_random_exit(self):
    #     config = Config("./tests/config_templates/valid/random_exit.yml").services[0]
    #     service = Service(**config)
    #     await service.start()
    #     print(service.status)
    #     self.assertEqual(service.status, {"random exit": SubProcess.State.EXITED})

    async def test_prog_exits_before_starttime_with_one_retry(self):
        config = Config(
            "./tests/config_templates/valid/test_prog_exits_before_starttime_with_one_retry.yml"
        ).services[0]
        service = Service(**config)
        await service.start()
        await service.wait()
        with open("/tmp/random_start_time.stdout", "r") as f:
            self.assertLessEqual(len(f.readlines()), 15)
        self.assertEqual(
            service.status,
            {"exits before starttime 1 retry": SubProcess.State.FATAL},
        )

    async def test_start_when_stopping_doesnt_work(self):
        config = Config(
            "./tests/config_templates/valid/test_start_when_stopping.yml"
        ).services[0]
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status, {"start when stopping": SubProcess.State.RUNNING}
        )
        asyncio.create_task(service.stop())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status, {"start when stopping": SubProcess.State.STOPPING}
        )
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status, {"start when stopping": SubProcess.State.STOPPING}
        )
