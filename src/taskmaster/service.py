from asyncio.subprocess import Process
from io import TextIOWrapper
from typing import List, Dict, Any, Optional, Self
import subprocess
from enum import Enum
import asyncio
import contextlib

from .utils.logger import logger
from .utils.config import Signal, AutoRestart


class SubProcess:
    """Represents a subprocess of a service."""

    class State(Enum):
        """
        The state of a process.
        See http://supervisord.org/subprocess.html#process-states for more information.
        """

        STOPPED = "Stopped"
        STARTING = "Starting"
        RUNNING = "Running"
        BACKOFF = "Backoff"
        STOPPING = "Stopping"
        EXITED = "Exited"
        FATAL = "Fatal"

    def __init__(
        self,
        parent_name: str,
        cmd: str,
        umask: int | None,
        workingdir: str | None,
        stdout: int | TextIOWrapper = subprocess.DEVNULL,
        stderr: int | TextIOWrapper = subprocess.DEVNULL,
        user: str | None = None,
        env: Dict[str, str] | None = None,
    ) -> None:
        self._parent_name = parent_name
        self._cmd = cmd
        self._umask = umask
        self._workingdir = workingdir
        self._stdout = stdout
        self._stderr = stderr
        self._user = user
        self._env = env
        self._process: Process | None = None
        self._state: SubProcess.State = self.State.STOPPED
        self._retries: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    # async def __del__(self) -> None:
    #     """
    #     Destructor for the SubProcess class.
    #     """
    #     if self._process is not None:
    #         self._process.kill()
    #         await self._process.wait()

    @property
    def state(self) -> State:
        """
        Gets the state of the subprocess.
        """
        return self._state

    @property
    def retries(self) -> int:
        """
        Gets the number of retries of the subprocess.
        """
        return self._retries

    @retries.setter
    def retries(self, value: int) -> None:
        """
        Sets the number of retries of the subprocess.
        """
        self._retries = value

    async def _poll(self) -> int | None:
        if not self._process:
            return
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._process.wait(), 1e-6)
        return self._process.returncode

    async def start(self, retries: int, starttime: int) -> Self:
        """
        Starts the subprocess.

        Retries will take increasingly more time depending on the number of subsequent attempts made,
        adding one second each time. So if you set startretries=3, taskmaster will wait one,
        two and then three seconds between each restart attempt, for a total of 5 seconds.
        """
        if self._process and await self._poll() is None:
            logger.warning(
                f"Process {self._parent_name}-{self._process.pid} is already running."
            )
            return self

        success: bool = False

        while not success:
            try:
                if self._cmd is None:
                    raise ValueError("Command is not provided.")
                self._process = await asyncio.create_subprocess_exec(
                    *self._cmd.split(),
                    cwd=self._workingdir,
                    env=self._env,
                    stdout=self._stdout,
                    stderr=self._stderr,
                    umask=self._umask or 0,
                    user=self._user,
                )
                self._state = self.State.STARTING
                logger.info(
                    f"Starting process: {self._parent_name} with pid: {self._process.pid}"
                )

                for _ in range(starttime * 10):
                    if await self._poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                if starttime == 0 or await self._poll() is None:
                    logger.info(
                        f"Process {self._parent_name}-{self._process.pid} is now running."
                    )
                    self._state = self.State.RUNNING
                    success = True
                else:
                    logger.error(
                        f"Process {self._parent_name}-{self._process.pid} has exited before {starttime} seconds."
                    )
                    retries -= 1

            except Exception as e:
                retries -= 1
                self.retries += 1
                self._state = self.State.BACKOFF
                logger.error(f"Failed to start process {self._parent_name}")
                logger.debug(e)

            if retries <= 0 or success:
                break

            logger.info(
                f"Retrying to start process {self._parent_name} in {self._retries} seconds."
            )
            logger.info(f"Retries left: {retries}")
            await asyncio.sleep(self._retries + 1)

        if not success:
            self._state = self.State.FATAL

        return self

    async def wait(self) -> Self:
        """
        Waits for the subprocess to finish.

        Assumes the subprocess has been started.
        """

        if self._process is None or (
            self._state != self.State.RUNNING and self._state != self.State.EXITED
        ):
            logger.debug(f"Process {self._parent_name} is not started.")
            logger.debug(f"Process {self._parent_name} state is {self._state.name}")
            return self

        logger.debug(
            f"Waiting for process {self._parent_name}-{self._process.pid} to finish."
        )
        await self._process.wait()
        logger.info(f"Process {self._parent_name}-{self._process.pid} exited.")
        self._state = self.State.EXITED
        return self

    async def stop(self, stopsignal: str | Signal, stoptime: int) -> Self:
        """
        Tries to stop the process using the given signal.
        If the process is not stopped after stoptime seconds, it will be killed
        """
        if not isinstance(stopsignal, Signal):
            stopsignal = Signal[str(stopsignal)]

        if self._process is None or (
            self._state != self.State.RUNNING and self._state != self.State.STARTING
        ):
            logger.warning(
                f"Process {self._parent_name} with pid {self._process.pid if self._process else None}: Stopped called when the process is not running"
            )
            return self

        self._process.send_signal(stopsignal.value)
        self._state = self.State.STOPPING
        for _ in range(stoptime * 10):
            await asyncio.sleep(0.1)
            if await self._poll():
                break
        if not await self._poll():
            self._process.kill()
        self.retries = 0
        self._state = self.State.STOPPED
        return self

    async def autorestart(
        self,
        exitcodes: List[int],
        retries: int,
        starttime: int,
        autorestart: str,
    ) -> Self:
        """
        Restarts the subprocess.

        When a process is in the EXITED state, it will automatically restart:
        - never if its autorestart parameter is set to false.
        - unconditionally if its autorestart parameter is set to true.
        - conditionally if its autorestart parameter is set to unexpected.
            If it exited with an exit code that doesn't match one of the exit codes defined in the exitcodes
            configuration parameter for the process, it will be restarted.
        """
        if self._process is None:
            logger.warning(f"Process {self._parent_name} is not running.")
            return self

        if self.state != self.State.EXITED:
            logger.warning(
                f"Process {self._parent_name} with pid {self._process.pid} is not exited."
            )
            return self

        if (
            self._process.returncode not in exitcodes
            and autorestart == AutoRestart.UNEXPECTED.value
        ) or autorestart == AutoRestart.ALWAYS.value:
            logger.info(
                f"Restarting process {self._parent_name} with pid: {self._process.pid}"
            )
            self.retries += 1
            await self.start(retries=retries, starttime=starttime)
        else:
            logger.debug(
                f"Process {self._parent_name} with pid {self._process.pid} doesn't need to be restarted"
            )
        return self

    def flush(self) -> None:
        """
        Flushes the stdout and stderr buffers.
        """
        if type(self._stdout) is TextIOWrapper:
            self._stdout.flush()

        if type(self._stderr) is TextIOWrapper:
            self._stderr.flush()


class Service:
    """
    Represents a service that can be managed by the service handler.
    """

    class Config:
        """
        The configuration of a service.
        """

        def __init__(
            self,
            **config: Dict[str, Any],
        ) -> None:
            self.name: str
            self.cmd: str
            self.numprocs: int
            self.umask: int
            self.workingdir: str
            self.autostart: bool
            self.autorestart: str
            self.exitcodes: List[int]
            self.startretries: int
            self.starttime: int
            self.stoptime: int
            self.stderr: str
            self.stdout: str
            self.stopsignal: str
            self.user: str
            self.env: Dict[str, str]
            self.__dict__.update(config)

        def __iter__(self) -> Any:
            return iter(self.__dict__.items())

    def __init__(
        self,
        **config: Dict[str, Any],
    ) -> None:
        """
        Initializes a new instance of the Program class.
        Will automatically start the service if autostart is set to True.

        Args:
            **config: The configuration parameters for the service.
        """
        self._config = self.Config(**config)
        self._processes: List[SubProcess] = []
        self._start_tasks: List[asyncio.Task] = []
        self._wait_tasks: List[asyncio.Task] = []

        self._init_stdout()
        self._init_stderr()

        self._create_subprocesses(num=self._config.numprocs)

    def __del__(self) -> None:
        """
        Destructor for the Program class.
        """
        if type(self.stdout) is TextIOWrapper:
            self.stdout.close()

        if type(self.stderr) is TextIOWrapper:
            self.stderr.close()

    def _init_stdout(self) -> None:
        """
        Initializes the stdout file for the service.
        """
        self.stdout: int | TextIOWrapper = subprocess.DEVNULL

        try:
            if self._config.stdout is not None:
                self.stdout = open(self._config.stdout, "w")
        except IOError:
            logger.warning(
                f"Failed to open stdout file: {self._config.stdout} - Defaulting to DEVNULL."
            )

    def _init_stderr(self) -> None:
        """
        Initializes the stderr file for the service.
        """
        self.stderr: int | TextIOWrapper = subprocess.DEVNULL

        try:
            if self._config.stderr is not None:
                self.stderr = open(self._config.stderr, "w")
        except IOError:
            logger.warning(
                f"Failed to open stderr file: {self._config.stderr} - Defaulting to DEVNULL."
            )

    def __str__(self) -> str:
        return f"Program(name={self._config.name}, command={self._config.cmd}, numprocs={self._config.numprocs})"

    def __repr__(self) -> str:
        return f"Program(name={self._config.name}, command={self._config.cmd}, numprocs={self._config.numprocs})"

    @property
    def config(self) -> Config:
        """
        Gets the configuration parameters for the service.

        Returns:
            The configuration parameters as a dictionary.
        """
        return self._config

    @config.setter
    def config(self, config: Dict[Any, Any]) -> Config:
        """
        Sets the configuration parameters for the service.

        Args:
            config: The new configuration parameters as a dictionary.
        """
        self._config = self.Config(**config)
        return self.config

    async def autostart(self) -> None:
        """
        Autostart the service if necessary.

        Always call this at the start of your loop.
        """
        if self._config.autostart:
            await self.start()
            logger.info(f"Service {self._config.name} autostarted.")

    async def _on_subprocess_started(self, task: asyncio.Task) -> object:
        """
        Wait for the subprocess to run and autorestart if necessary.
        """
        subprocess: SubProcess = await task
        await subprocess.wait()
        while (
            subprocess.state == SubProcess.State.EXITED
            and subprocess.retries < self._config.startretries
        ):
            logger.debug(f"{self._config.name}: Checking if an autorestart is required")
            await asyncio.sleep(subprocess.retries + 1)
            subprocess = await subprocess.autorestart(
                exitcodes=self._config.exitcodes,
                retries=self._config.startretries,
                starttime=self._config.starttime,
                autorestart=self._config.autorestart,
            )
            if subprocess.state == SubProcess.State.EXITED:
                logger.debug(f"{self._config.name}: No autorestart required")
                return
            await subprocess.wait()

        if subprocess.retries >= self._config.startretries:
            logger.error(f"{self._config.name}: Max retry attempt exceeded")
            subprocess._state = SubProcess.State.FATAL

        subprocess.retries = 0
        logger.debug(f"Removing task {task} from start_tasks")
        self._start_tasks.remove(task)

    def _create_subprocesses(self, num: int) -> None:
        for _ in range(num):
            subprocess: SubProcess = SubProcess(
                parent_name=self._config.name,
                cmd=self._config.cmd,
                umask=self._config.umask,
                workingdir=self._config.workingdir,
                stdout=self.stdout,
                stderr=self.stderr,
                user=self._config.user,
                env=self._config.env,
            )
            self._processes.append(subprocess)

    async def start(self) -> None:
        """
        Starts the service.
        """
        for process in self._processes:
            if (
                process.state != SubProcess.State.RUNNING
                and process.state != SubProcess.State.STARTING
                and process.state != SubProcess.State.STOPPING
            ):
                if process._process:
                    logger.debug(
                        f"Removing process {process._parent_name} with pid {process._process.pid} from processes"
                    )
                self._processes.remove(process)

        self._create_subprocesses(num=self._config.numprocs - len(self._processes))
        self._start_tasks: List[asyncio.Task] = []
        self._wait_tasks: List[asyncio.Task] = []
        for process in self._processes:
            self._start_tasks += [
                asyncio.create_task(
                    process.start(
                        retries=self._config.startretries,
                        starttime=self._config.starttime,
                    )
                )
            ]
            self._wait_tasks += [
                asyncio.create_task(self._on_subprocess_started(self._start_tasks[-1]))
            ]

        await asyncio.gather(*self._start_tasks)

    async def wait(self) -> None:
        """
        Waits for the service to finish.

        Pretty much only useful for testing.
        """
        await asyncio.gather(*self._wait_tasks)

    async def stop(self) -> None:
        """
        Stops the service.
        """
        for task in self._start_tasks:
            task.cancel()

        for task in self._wait_tasks:
            task.cancel()

        self._start_tasks = []
        self._wait_tasks = []
        _stop_tasks: List[asyncio.Task] = []

        for process in self._processes:
            _stop_tasks += [
                asyncio.create_task(
                    process.stop(
                        stopsignal=self._config.stopsignal,
                        stoptime=self._config.stoptime,
                    )
                )
            ]

        await asyncio.gather(*_stop_tasks)

    async def restart(self) -> None:
        """
        Restarts the service.
        """
        with contextlib.suppress(RuntimeError):
            await self.stop()
        await self.start()

    @property
    def status(self) -> dict[str, SubProcess.State]:
        """
        Returns the status of the service.
        """
        return {process._parent_name: process.state for process in self._processes}

    def flush(self) -> None:
        """
        Flushes the stdout and stderr buffers.
        """
        if type(self.stdout) is TextIOWrapper:
            self.stdout.flush()

        if type(self.stderr) is TextIOWrapper:
            self.stderr.flush()


class ServiceHandler:
    """
    Represents a service that manages services and their configurations.
    """

    class Config:
        """
        The configuration of a service handler.
        """

        def __init__(
            self,
            **config: Dict[Any, Any],
        ) -> None:
            self.services: List[Service.Config] = []
            self.__dict__.update(config)

        def __iter__(self) -> Any:
            return iter(self.__dict__.items())

    def __init__(
        self,
        **config: Dict[Any, Any],
    ) -> None:
        """
        Initializes a new instance of the ServiceHandler class.

        Args:
            **config: The configuration parameters for the service handler.
        """
        self._config: ServiceHandler.Config = self.Config(**config)
        self._services: List[Service] = []

        for service in self._config.services:
            self._services.append(Service(**dict(service)))

    def status(self) -> list[dict[str, str]]:
        """
        Displays the status of all services.
        """
        ret: list[dict[str, str]] = []
        for service in self._services:
            status = dict(
                {
                    "name": service.config.name,
                    "cmd": service.config.cmd,
                }
            )
            count = 0
            for process in service._processes:
                count += 1
                status[f"process_{count}"] = process.state.value
            ret.append(
                status,
            )
        return ret

    async def start(self, service_names: Optional[List[str]] = None):
        """
        Starts one or multiple services.

        Args:
            service_names: The name of the services to start.
        """
        if not service_names:
            service_names = [service.config.name for service in self._services]

        logger.debug(f"Starting services: {service_names}")
        for service in self._services:
            if service.config.name in service_names:
                asyncio.create_task(service.start())

    async def stop(self, service_names: Optional[List[str]] = None):
        """
        Stops one or multiple services.

        Args:
            service_names: The name of the services to stop.
        """
        if not service_names:
            service_names = [service.config.name for service in self._services]

        for service in self._services:
            if service.config.name in service_names:
                asyncio.create_task(service.stop())

    async def restart(self, service_names: Optional[List[str]] = None):
        """
        Restarts one or multiple services.

        Args:
            service_names: The name of the services to restart.
        """
        if not service_names:
            service_names = [service.config.name for service in self._services]

        for service in self._services:
            if service.config.name in service_names:
                asyncio.create_task(service.restart())

    async def autostart(self) -> None:
        """
        Autostart all services.
        """
        logger.info("Autostarting services.")
        for service in self._services:
            asyncio.create_task(service.autostart())

    @property
    def config(self) -> Config:
        """
        Gets the configuration parameters for the service.

        Returns:
            The configuration parameters.
        """
        return self._config

    @config.setter
    def config(self, config: Dict[Any, Any]) -> Config:
        """
        Sets the configuration parameters for the service.

        Args:
            config: The new configuration parameters as a dictionary.

        Returns:
            The configuration parameters.
        """
        self._config = self.Config(**config)
        return self.config

    def flush(self, service_name: str) -> None:
        """
        Flushes the stdout and stderr buffers of the given service.
        """
        for service in self._services:
            if service.config.name == service_name:
                service.flush()
                return
        logger.warning(f"Service {service_name} not found.")
