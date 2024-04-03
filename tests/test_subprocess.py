import unittest
import asyncio

from taskmaster.service import SubProcess
from taskmaster.utils.config import Signal, AutoRestart


class TestSubprocess(unittest.IsolatedAsyncioTestCase):
    async def test_start_with_working_config(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")

    async def test_start_with_working_config_with_starttime(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 1.1",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=1)
        self.assertEqual(subprocess.state.name, "RUNNING")

    async def test_start_with_working_config_with_starttime_equal(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 2",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=2)
        self.assertEqual(subprocess.state.name, "FATAL")  # ptetre random ca

    async def test_start_with_nonexistent_workingdir(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/nonexistent",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    async def test_start_with_nonexistent_cmd(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="nonexistent",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    async def test_start_with_wrong_user(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
            user="nonexistent",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    async def test_start_twice(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")

    async def test_redirect_stdout(self):
        with open("/tmp/stdout.log", "w+") as f:
            subprocess: SubProcess = SubProcess(
                parent_name="echo",
                cmd="echo Hello, World!",
                umask=0o77,
                workingdir="/tmp",
                stdout=f,
            )
            await subprocess.start(retries=0, starttime=0)
            await subprocess.wait(0)
            self.assertEqual(subprocess.state.name, "EXITED")
        with open("/tmp/stdout.log", "r") as f:
            self.assertEqual(f.read(), "Hello, World!\n")

    async def test_redirect_stderr(self):
        with open("/tmp/stderr.log", "w+") as f:
            subprocess: SubProcess = SubProcess(
                parent_name="echo",
                cmd="ls /nonexistent",
                umask=0o77,
                workingdir="/tmp",
                stderr=f,
            )
            await subprocess.start(retries=0, starttime=0)
            await subprocess.wait(0)
            self.assertEqual(subprocess.state.name, "EXITED")
        with open("/tmp/stderr.log", "r") as f:
            self.assertEqual(
                f.read(),
                "ls: cannot access '/nonexistent': No such file or directory\n",
            )

    async def test_stop(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.stop(stopsignal=Signal.QUIT, stoptime=0)
        self.assertEqual(subprocess.state.name, "STOPPED")

    async def test_autorestart_always(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.wait(1)
        self.assertEqual(subprocess.state.name, "EXITED")
        await subprocess.autorestart(
            exitcodes=[0], starttime=0, retries=1, autorestart=AutoRestart.ALWAYS.value
        )
        self.assertEqual(subprocess.state.name, "RUNNING")

    async def test_autorestart_unexpected(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.wait(1)
        self.assertEqual(subprocess.state.name, "EXITED")
        await subprocess.autorestart(
            exitcodes=[1],
            starttime=0,
            retries=1,
            autorestart=AutoRestart.UNEXPECTED.value,
        )
        self.assertEqual(subprocess.state.name, "RUNNING")

    async def test_autorestart_never(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.wait(1)
        self.assertEqual(subprocess.state.name, "EXITED")
        await subprocess.autorestart(
            exitcodes=[0], starttime=0, retries=1, autorestart=AutoRestart.NEVER.name
        )
        self.assertEqual(subprocess.state.name, "EXITED")

    def test_state_is_stopped_if_not_started(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        self.assertEqual(subprocess.state.name, "STOPPED")

    async def test_state_is_stopped_if_stopped(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.stop(stopsignal=Signal.TERM, stoptime=0)
        self.assertEqual(subprocess.state.name, "STOPPED")

    # This test should not take more than 1 second
    async def test_fails_if_starttime_too_long(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 1",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=100)
        self.assertEqual(subprocess.state.name, "FATAL")

    # Should take 3 seconds with retries
    async def test_start_multiple_retries(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="nonexistent",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=2, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")
        self.assertEqual(subprocess._retries, 2)

    async def test_start_multiple_retries_with_working_config(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=3, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        self.assertEqual(subprocess._retries, 0)

    async def test_stop_right_after_start(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        task = asyncio.create_task(subprocess.start(retries=0, starttime=0))
        await asyncio.sleep(0.01)
        await subprocess.stop(stopsignal=Signal.TERM, stoptime=0)
        await task
        self.assertEqual(subprocess.state.name, "STOPPED")

    async def test_delete(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        await subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        await subprocess.delete()
        self.assertNotEqual(subprocess._process.returncode, None)
