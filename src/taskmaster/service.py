from io import TextIOWrapper
from multiprocessing import Pool
from typing import List, Dict, Any, Optional
import subprocess
from enum import Enum
import time

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
        umask: int,
        workingdir: str,
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
        self._process: subprocess.Popen | None = None
        self._state: SubProcess.State = self.State.STOPPED
        self._retries: int = 0

    def __del__(self) -> None:
        """
        Destructor for the SubProcess class.
        """
        if self._process is not None:
            self._process.kill()
            self._process.wait()

    @property
    def state(self) -> State:
        """
        Gets the state of the subprocess.
        """
        return self._state

    def start(self, retries: int, starttime: int) -> State:
        """
        Starts the subprocess.

        Retries will take increasingly more time depending on the number of subsequent attempts made,
        adding one second each time. So if you set startretries=3, taskmaster will wait one,
        two and then three seconds between each restart attempt, for a total of 5 seconds.
        """
        if self._process and self._process.poll() is None:
            logger.warning(
                f"Process {self._parent_name}-{self._process.pid} is already running."
            )
            return self.state

        success: bool = False
        self._retries = 0

        while not success:
            try:
                if self._cmd is None:
                    raise ValueError("Command is not provided.")
                self._process = subprocess.Popen(
                    self._cmd.split(),
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
                    if self._process.poll() is not None:
                        break
                    time.sleep(0.1)
                if self._process.poll() is None:
                    logger.info(
                        f"Process {self._parent_name}-{self._process.pid} is now running."
                    )
                    self._state = self.State.RUNNING
                    success = True
                else:
                    logger.error(
                        f"Process {self._parent_name}-{self._process.pid} has exited before {starttime}."
                    )

            except Exception as e:
                retries -= 1
                self._retries += 1
                self._state = self.State.BACKOFF
                logger.error(f"Failed to start process {self._parent_name}")
                logger.debug(e)

            if retries <= 0 or success:
                break

            logger.info(
                f"Retrying to start process {self._parent_name} in {self._retries} seconds."
            )
            logger.info(f"Retries left: {retries}")
            time.sleep(self._retries + 1)
            # asyncio.sleep(self._retries + 1)

        if not success:
            self._state = self.State.FATAL

        return self.state

    def wait(self) -> State:
        """
        Waits for the subprocess to finish.

        Assumes the subprocess is already running.
        """

        if self._process is None or self._state != self.State.RUNNING:
            logger.debug(f"Process {self._parent_name} is not running.")
            raise RuntimeError("Process is not running.")

        logger.debug(
            f"Waiting for process {self._parent_name}-{self._process.pid} to finish."
        )
        self._process.wait()
        logger.debug(f"Process {self._parent_name}-{self._process.pid} exited.")
        self._state = self.State.EXITED
        return self.state

    def stop(self, stopsignal: Signal, stoptime: int) -> State:
        """
        Tries to stop the program using the given signal.
        If the program is not stopped after stoptime seconds, the process will be killed
        """
        if self._process is None:
            raise RuntimeError("Process is not running.")

        self._process.send_signal(stopsignal.value)
        self._state = self.State.STOPPING
        for _ in range(stoptime * 10):
            time.sleep(0.1)
            if self._process.poll():
                break
        if not self._process.poll():
            self._process.kill()
        print(f"Return codes: {self._process.poll()}")
        self._state = self.State.STOPPED
        return self.state

    def autorestart(
        self,
        exitcodes: List[int],
        retries: int,
        starttime: int,
        autorestart: AutoRestart,
    ) -> State:
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
            raise RuntimeError("Process is not running.")

        if self.state != self.State.EXITED:
            logger.warning(
                f"Process {self._parent_name} with pid {self._process.pid} is not exited."
            )
            return self.state

        if (
            self._process.returncode not in exitcodes
            and autorestart == AutoRestart.UNEXPECTED
        ) or autorestart == AutoRestart.ALWAYS:
            logger.info(
                f"Restarting process {self._parent_name} with pid: {self._process.pid}"
            )
            self.start(retries=retries, starttime=starttime)
        return self.state


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
            self.name: str | None = None
            self.cmd: str | None = None
            self.numprocs: int | None = None
            self.umask: int | None = None
            self.workingdir: str | None = None
            self.autostart: bool | None = None
            self.autorestart: AutoRestart | None = None
            self.exitcodes: List[int] | None = None
            self.startretries: int | None = None
            self.starttime: int | None = None
            self.stopsignal: Signal | None = None
            self.stoptime: int | None = None
            self.stdout: str | None = None
            self.stderr: str | None = None
            self.user: str | None = None
            self.env: Dict[str, str] | None = None
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
        self._processes: List[subprocess.Popen] = []
        self._pool = Pool(self._config.numprocs)

        self._init_stdout()
        self._init_stderr()

        if self._config.autostart:
            self.start()

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

    def start(self) -> None:
        """
        Starts the service.
        """
        pass

    def stop(self) -> None:
        """
        Stops the service.
        """
        pass

    def restart(self) -> None:
        """
        Restarts the service.
        """
        pass

    def reload(self) -> None:
        """
        Reloads the configuration of the service.
        """
        pass


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

    def status(self):
        """
        Displays the status of all services.
        """
        pass

    def start(self, service_names: Optional[List[str]] = None):
        """
        Starts one or multiple services.

        Args:
            service_names: The name of the services to start.
        """
        for service in self._services:
            if service_names and service.config.name in service_names:
                service.start()

    def stop(self, service_names: Optional[List[str]] = None):
        """
        Stops one or multiple services.

        Args:
            service_names: The name of the services to stop.
        """
        for service in self._services:
            if service_names and service.config.name in service_names:
                service.stop()

    def restart(self, service_names: Optional[List[str]] = None):
        """
        Restarts one or multiple services.

        Args:
            service_names: The name of the services to restart.
        """
        for service in self._services:
            if service_names and service.config.name in service_names:
                service.restart()

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

    def reload(self, service_names: Optional[List[str]] = None) -> None:
        """
        Reloads the configuration of one or multiple services.
        """
        for service in self._services:
            if service_names and service.config.name in service_names:
                service.reload()
