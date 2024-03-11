import unittest
import threading
import time

from src.taskmaster.service import SubProcess
from src.taskmaster.utils.config import Signal, AutoRestart


class TestSubprocess(unittest.TestCase):
    def test_start_with_working_config(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")

    def test_start_with_nonexistent_workingdir(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/nonexistent",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    def test_start_with_nonexistent_cmd(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="nonexistent",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    def test_start_with_wrong_user(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
            user="nonexistent",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")

    def test_start_twice(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")

    def test_redirect_stdout(self):
        with open("/tmp/stdout.log", "w+") as f:
            subprocess: SubProcess = SubProcess(
                parent_name="echo",
                cmd="echo Hello, World!",
                umask=0o77,
                workingdir="/tmp",
                stdout=f,
            )
            subprocess.start(retries=0, starttime=0)
            self.assertEqual(subprocess.state.name, "RUNNING")
            subprocess.wait()
            self.assertEqual(subprocess.state.name, "EXITED")
        with open("/tmp/stdout.log", "r") as f:
            self.assertEqual(f.read(), "Hello, World!\n")

    def test_redirect_stderr(self):
        with open("/tmp/stderr.log", "w+") as f:
            subprocess: SubProcess = SubProcess(
                parent_name="echo",
                cmd="ls /nonexistent",
                umask=0o77,
                workingdir="/tmp",
                stderr=f,
            )
            subprocess.start(retries=0, starttime=0)
            self.assertEqual(subprocess.state.name, "RUNNING")
            subprocess.wait()
            self.assertEqual(subprocess.state.name, "EXITED")
        with open("/tmp/stderr.log", "r") as f:
            self.assertEqual(
                f.read(),
                "ls: cannot access '/nonexistent': No such file or directory\n",
            )

    def test_stop(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.stop(stopsignal=Signal.QUIT, stoptime=0)
        self.assertEqual(subprocess.state.name, "STOPPED")

    def test_autorestart_always(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.wait()
        self.assertEqual(subprocess.state.name, "EXITED")
        subprocess.autorestart(
            exitcodes=[0], starttime=0, retries=1, autorestart=AutoRestart.ALWAYS
        )
        self.assertEqual(subprocess.state.name, "RUNNING")

    def test_autorestart_unexpected(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.wait()
        self.assertEqual(subprocess.state.name, "EXITED")
        subprocess.autorestart(
            exitcodes=[1], starttime=0, retries=1, autorestart=AutoRestart.UNEXPECTED
        )
        self.assertEqual(subprocess.state.name, "RUNNING")

    def test_autorestart_never(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 0.1",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.wait()
        self.assertEqual(subprocess.state.name, "EXITED")
        subprocess.autorestart(
            exitcodes=[0], starttime=0, retries=1, autorestart=AutoRestart.NEVER
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

    def test_state_is_stopped_if_stopped(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        subprocess.stop(stopsignal=Signal.TERM, stoptime=0)
        self.assertEqual(subprocess.state.name, "STOPPED")

    # This test should not take more than 1 second
    def test_fails_if_starttime_too_long(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 1",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=0, starttime=100)
        self.assertEqual(subprocess.state.name, "FATAL")

    # Should take 3 seconds with retries
    def test_start_multiple_retries(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="nonexistent",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=2, starttime=0)
        self.assertEqual(subprocess.state.name, "FATAL")
        self.assertEqual(subprocess._retries, 2)

    def test_start_multiple_retries_with_working_config(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        subprocess.start(retries=3, starttime=0)
        self.assertEqual(subprocess.state.name, "RUNNING")
        self.assertEqual(subprocess._retries, 0)

    def test_stop_right_after_start(self):
        subprocess: SubProcess = SubProcess(
            parent_name="sleep",
            cmd="sleep 5",
            umask=0o77,
            workingdir="/tmp",
        )
        start_thread = threading.Thread(target=subprocess.start, args=(0, 3))
        start_thread.start()
        time.sleep(0.1)
        subprocess.stop(stopsignal=Signal.TERM, stoptime=0)
        self.assertEqual(subprocess.state.name, "STOPPED")
