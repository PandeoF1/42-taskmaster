import unittest
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from taskmaster.service import Service, SubProcess
from taskmaster.utils.config import Config
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
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)

    async def test_start_await(self):
        config = self.config
        service = Service(**config)
        await service.start()
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)

    async def test_stop_async(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        asyncio.create_task(service.stop())
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)

    async def test_stop_await(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await service.stop()
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)

    async def test_restart(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        asyncio.create_task(service.restart())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)

    async def test_restart_when_not_started_yet(self):
        config = self.config
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.01)
        asyncio.create_task(service.restart())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)

    async def test_autorestart_always(self):
        config = self.config
        config["autorestart"] = "always"
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)

    async def test_autorestart_unexpected_should_restart(self):
        config = self.config
        config["autorestart"] = "unexpected"
        config["exitcodes"] = [42]
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)

    async def test_autorestart_unexpected_shouldnt_restart(self):
        config = self.config
        config["autorestart"] = "unexpected"
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        await asyncio.sleep(1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        await asyncio.sleep(1)
        self.assertNotEqual(service.status.get("process_1"), SubProcess.State.STARTING)

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
            self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)
            await asyncio.sleep(1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            await asyncio.sleep(1)
            if i == retries:
                break
            self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
            await asyncio.sleep(i + 1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.FATAL)

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
            self.assertEqual(service.status.get("process_1"), SubProcess.State.STARTING)
            await asyncio.sleep(1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            await asyncio.sleep(1)
            if i == retries:
                break
            self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
            await asyncio.sleep(i + 1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.FATAL)

    async def test_autostart(self):
        config = self.config
        config["autostart"] = True
        service = Service(**config)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)
        asyncio.create_task(service.autostart())
        await asyncio.sleep(0.1)
        self.assertNotEqual(service.status.get("process_1"), SubProcess.State.STOPPED)

    async def test_umask_003(self):
        config = Config("./tests/config_templates/valid/umask03.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        with open("/tmp/umask003.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 03\n")

    async def test_umask_077(self):
        config = Config("./tests/config_templates/valid/umask077.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        with open("/tmp/umask077.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 077\n")

    async def test_umask_007(self):
        config = Config("./tests/config_templates/valid/umask07.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        with open("/tmp/umask007.stdout") as f:
            self.assertEqual(f.read(), "---- umask test ----\numask: 07\n")

    async def test_stdout(self):
        config = Config("./tests/config_templates/valid/stdout.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        with open("/tmp/stdout.stdout") as f:
            self.assertTrue("---- stdout test ----" in f.read())

    async def test_stderr(self):
        config = Config("./tests/config_templates/valid/stderr.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
        with open("/tmp/stderr.stderr") as f:
            self.assertTrue("---- stderr test ----" in f.read())

    async def test_stdout_no_file(self):
        os.remove("/tmp/stdout.stdout")
        config = Config("./tests/config_templates/valid/stdout_no_file.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
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
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)
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
            service.status.get("process_1"),
            SubProcess.State.FATAL,
        )

    async def test_start_when_stopping_doesnt_work(self):
        config = Config(
            "./tests/config_templates/valid/test_start_when_stopping.yml"
        ).services[0]
        service = Service(**config)
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status.get("process_1"), SubProcess.State.RUNNING
        )
        asyncio.create_task(service.stop())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status.get("process_1"), SubProcess.State.STOPPING
        )
        asyncio.create_task(service.start())
        await asyncio.sleep(0.1)
        self.assertEqual(
            service.status.get("process_1"), SubProcess.State.STOPPING
        )

    async def test_reload_remove_subprocesses(self):
        config = Config("./tests/config_templates/valid/test_reload.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        config["numprocs"] = 2
        service.config = config
        await service.reload()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        self.assertNotEqual(service.status.get("process_3"), SubProcess.State.RUNNING)
        self.assertEqual(len(service._processes), 2)

    async def test_reload_change_cmd(self):
        config = Config("./tests/config_templates/valid/test_reload.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        config["cmd"] = "sleep 2"
        service.config = config
        await service.reload()
        self.assertEqual(service._processes[0]._cmd, "sleep 2")
        self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)
        await service.start()
        await asyncio.sleep(1.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.EXITED)

    async def test_reload_change_nothing(self):
        config = Config("./tests/config_templates/valid/test_reload.yml").services[0]
        service = Service(**config)
        await service.start()
        await asyncio.sleep(0.1)
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
        service.config = config
        await service.reload()
        self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)

    async def test_send_email_on_start_one_proc(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            self.assertEqual(email_mock.send_start.call_count, 1)
            email_mock.send_start.assert_called_with(
                config.get("name"), SubProcess.State.RUNNING.name
            )

    async def test_send_email_on_start_multiple_procs(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        config["numprocs"] = 8
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            self.assertEqual(service.status.get("process_2"), SubProcess.State.RUNNING)
            self.assertEqual(email_mock.send_start.call_count, 8)
            email_mock.send_start.assert_called_with(
                config.get("name"), SubProcess.State.RUNNING.name
            )

    async def test_send_email_on_stop_one_proc(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            await service.stop()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)
            self.assertEqual(email_mock.send_stop.call_count, 1)
            email_mock.send_stop.assert_called_with(
                config.get("name"), SubProcess.State.STOPPED.name
            )

    async def test_send_email_on_stop_multiple_procs(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        config["numprocs"] = 8
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.RUNNING)
            await service.stop()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.STOPPED)
            self.assertEqual(email_mock.send_stop.call_count, 8)
            email_mock.send_stop.assert_called_with(
                config.get("name"), SubProcess.State.STOPPED.name
            )

    async def test_send_email_on_fatal_one_proc(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        config["autorestart"] = "never"
        config["startretries"] = 0
        config["starttime"] = 10
        config["cmd"] = "dontexist"
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.FATAL)
            self.assertEqual(email_mock.send_exited.call_count, 1)
            email_mock.send_exited.assert_called_with(
                config.get("name"), SubProcess.State.FATAL.name
            )

    async def test_send_email_on_fatal_multiple_procs(self):
        config = Config("./tests/config_templates/valid/test_send_email.yml").services[0]
        config["numprocs"] = 8
        config["autorestart"] = "never"
        config["startretries"] = 0
        config["starttime"] = 10
        config["cmd"] = "dontexist"
        email_mock = AsyncMock(name="taskmaster.utils.email.Email")
        with patch("taskmaster.utils.email.Email", email_mock):
            service = Service(email=email_mock, **config)
            await service.start()
            await asyncio.sleep(0.1)
            self.assertEqual(service.status.get("process_1"), SubProcess.State.FATAL)
            self.assertEqual(email_mock.send_exited.call_count, 8)
            email_mock.send_exited.assert_called_with(
                config.get("name"), SubProcess.State.FATAL.name
            )
