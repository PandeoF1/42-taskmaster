from asyncio.subprocess import Process
from io import TextIOWrapper
from typing import List, Dict, Any, Optional, Self
import subprocess
from enum import Enum
import asyncio
import contextlib

from .utils.logger import logger
from .utils.config import Signal, AutoRestart
from .utils.email import Email


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
        email: Email | None = None,
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
        self._email: Email | None = email

    async def delete(self) -> None:
        """
        Destructor for the SubProcess class.
        """
        try:
            if self._process and self._process.returncode is None:
                self._process.terminate()
                await self._process.wait()
        except ProcessLookupError as e:
            logger.error(f"Failed to terminate process {self._parent_name}: {e}")

    @property
    def state(self) -> State:
        """
        Gets the state of the subprocess.
        """
        return self._state

    @state.setter
    def state(self, value: State) -> None:
        """
        Sets the state of the subprocess.
        """
        self._state = value

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

    @property
    def config(self) -> Dict[str, Any]:
        """
        Gets the configuration parameters for the subprocess.

        Returns:
            The configuration parameters as a dictionary.
        """
        return {
            "cmd": self._cmd,
            "umask": self._umask,
            "workingdir": self._workingdir,
            "stdout": self._stdout,
            "stderr": self._stderr,
            "user": self._user,
            "env": self._env,
        }

    @config.setter
    def config(self, config: Dict[str, Any]) -> None:
        """
        Sets the configuration parameters for the subprocess.

        Args:
            config: The new configuration parameters as a dictionary.
        """
        self._cmd = config["cmd"]
        self._umask = config["umask"]
        self._workingdir = config["workingdir"]
        self._stdout = config["stdout"]
        self._stderr = config["stderr"]
        self._user = config["user"]
        self._env = config["env"]

    @property
    def email(self) -> Email | None:
        """
        Gets the email configuration.
        """
        return self._email

    @email.setter
    def email(self, email: Email | None) -> None:
        """
        Sets the email configuration.
        """
        self._email = email

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
                    if self._email:
                        asyncio.create_task(self._email.send_start(self._parent_name, self._state.name))
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
            if self._email:
                asyncio.create_task(
                    self._email.send_exited(self._parent_name, self._state.name)
                )

        return self

    async def wait(self, startretries: int) -> Self:
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
        logger.info(f"Process {self._parent_name}-{self._process.pid} ended.")
        if self.retries > 0 and self.retries >= startretries:
            logger.error(f"{self._parent_name}: Max retry attempt exceeded")
            self.state = SubProcess.State.FATAL
        else:
            logger.info(f"{self._parent_name}: Process exited with code {self._process.returncode}")
            self.state = SubProcess.State.EXITED
        if self._email:
            asyncio.create_task(self._email.send_exited(self._parent_name, self._state.name))
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
                f"Process {self._parent_name} with pid "
                f"{self._process.pid if self._process else None}: Stopped called when the process is not running"
            )
            return self

        self._process.send_signal(stopsignal.value)
        logger.info(f"Process {self._parent_name}: sending signal {stopsignal.name}")
        self._state = self.State.STOPPING
        for _ in range(stoptime * 10):
            await asyncio.sleep(0.1)
            if await self._poll():
                break
        if not await self._poll():
            logger.warning(f"Process {self._parent_name} unresponsive: killing forcefully")
            self._process.kill()
        self.retries = 0
        self._state = self.State.STOPPED
        logger.info(f"Process {self._parent_name} stopped successfully.")
        if self._email:
            asyncio.create_task(
                self._email.send_stop(self._parent_name, self._state.name)
            )
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
        email: Email | None = None,
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
        self._email: Email | None = email

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

    async def delete(self):
        """
        Destructor for the Service class.
        """
        logger.info(f"Deleting service {self._config.name}")
        for process in self._processes:
            await process.delete()
        self._processes.clear()
        logger.debug(f"Service {self._config.name} deleted.")

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
        return self._config

    async def reload(self) -> None:
        """
        Reloads the service configuration.

        Must be called after updating the configuration.
        """
        tasks: List[asyncio.Task] = []
        config: dict = dict(self._config)

        for _ in range(len(self._processes) - config["numprocs"]):
            process = self._processes.pop()
            tasks.append(asyncio.create_task(process.delete()))

        self._create_subprocesses(num=len(self._processes) - config["numprocs"])

        new_config = {
            "cmd": config["cmd"],
            "umask": config["umask"],
            "workingdir": config["workingdir"],
            "stdout": self.stdout,
            "stderr": self.stderr,
            "user": config["user"],
            "env": config["env"],
        }

        # The processes all have the same config, so why not take it from the first one
        if new_config != self._processes[0].config:
            for process in self._processes:
                tasks.append(asyncio.create_task(process.delete()))
            self._processes = []
            self._create_subprocesses(num=config["numprocs"])
        else:
            for process in self._processes:
                process.email = self._email

        tasks.append(asyncio.create_task(self.autostart()))

        await asyncio.gather(*tasks)

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
        await subprocess.wait(self._config.startretries)
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
            await subprocess.wait(self._config.startretries)

        subprocess.retries = 0
        logger.debug(f"Removing task {task} from start_tasks")
        self._start_tasks.remove(task)

    def _create_subprocesses(self, num: int) -> None:
        """Batch create subprocesses.

        Args:
            num (int): The number of subprocesses to create.
        """
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
                email=self._email,
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
        status: dict[str, Any] = dict(
            {
                "name": self.config.name,
                "cmd": self.config.cmd,
            }
        )
        count = 0
        for process in self._processes:
            count += 1
            status[f"process_{count}"] = process.state
        return status

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
        email: Email | None = None,
        **config: Dict[Any, Any],
    ) -> None:
        """
        Initializes a new instance of the ServiceHandler class.

        Args:
            **config: The configuration parameters for the service handler.
        """
        self._config: ServiceHandler.Config = self.Config(**config)
        self._services: List[Service] = []
        self._email: Email | None = email

        for service in self._config.services:
            self._services.append(Service(email=self._email, **dict(service)))

    @property
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
        return self._config

    async def reload(self, email: Email | None = None) -> Config:
        """
        Sets the configuration parameters for the service and reloads them.

        Args:
            config: The new configuration parameters as a dictionary.

        Returns:
            The configuration parameters.
        """
        tasks: List[asyncio.Task] = []

        config = dict(self._config)

        self._email = email

        # If the service is not in the new config, remove it
        for service in self._services.copy():
            if service.config.name not in [service.get("name") for service in config["services"]]:
                tasks.append(asyncio.create_task(service.delete()))
                self._services.remove(service)

        # If the service is still in the new config, update it
        for service in self._services:
            for service_config in config["services"]:
                if service.config.name == service_config.get("name"):
                    service.config = service_config
                    tasks.append(asyncio.create_task(service.reload()))
                    break

        # If the service is not in the old config, add it
        for service_config in config["services"]:
            if service_config.get("name") not in [
                service.config.name for service in self._services
            ]:
                self._services.append(Service(email=self._email, **dict(service_config)))

        tasks.append(asyncio.create_task(self.autostart()))
        self._config = self.Config(**config)
        return self.config

    def flush(self, service_name: str) -> None:
        """
        Flushes the stdout and stderr buffers of the given service.
        """
        for service in self._services:
            if service.config.name == service_name:
                return service.flush()
        logger.warning(f"Service {service_name} not found.")

    async def delete(self) -> None:
        """
        Destructor for the ServiceHandler class.
        """
        for service in self._services:
            await service.delete()
        self._services.clear()
        logger.debug("ServiceHandler deleted.")
