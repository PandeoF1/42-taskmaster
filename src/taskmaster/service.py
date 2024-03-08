from typing import List, Dict, Any, Optional
from enum import Enum
import subprocess


class ServiceConfig:
    """
    The configuration of a service.
    """

    def __init__(
        self,
        **config: Dict[Any, Any],
    ) -> None:
        self.services: List[ProgramConfig] = []
        self.__dict__.update(config)

    def __iter__(self) -> Any:
        return iter(self.__dict__.items())


"""
Program configuration example:
services:
  - name: "Sleep"
    cmd: "sleep 100"
    numprocs: 8 # min 1 max 32
    umask: 077
    workingdir: /tmp
    autostart: true
    autorestart: unexpected # always, never unexpected
    exitcodes:
      - 0
      - 2
    startretries: 3
    starttime: 5
    stopsignal: USR1 # On verra si on fait un template des sigevent
    stoptime: 10
    stdout: /tmp/sleep.stdout # Optionnal (if not present don't log)
    stderr: /tmp/sleep.stderr # Optionnal ("")
    user: # Optionnal
    env:
      STARTED_BY: taskmaster
      ANSWER: 42
"""


class ProgramConfig:
    """
    The configuration of a program.
    """

    class AutoStart(Enum):
        """
        Enumeration for auto restart options.

        Options:
        - ALWAYS: Always restart the service.
        - NEVER: Never restart the service.
        - UNEXPECTED: Restart the service only if it terminates unexpectedly.
        """

        ALWAYS = "always"
        NEVER = "never"
        UNEXPECTED = "unexpected"

    class Signal(Enum):
        """
        Enumeration for signals.

        Options:
        - USR1: User-defined signal 1.
        - USR2: User-defined signal 2.
        - INT: Interrupt signal.
        - TERM: Terminate signal.
        - HUP: Hangup signal.
        - QUIT: Quit signal.
        """

        USR1 = "USR1"
        USR2 = "USR2"
        INT = "INT"
        TERM = "TERM"
        HUP = "HUP"
        QUIT = "QUIT"

    def __init__(
        self,
        **config: Dict[str, Any],
    ) -> None:
        self.name: str | None = None
        self.cmd: str | None = None
        self.numprocs: int | None = None
        self.umask: int | None = None
        self.workingdir: str | None = None
        self.autostart: ProgramConfig.AutoStart | None = None
        self.autorestart: str | None = None
        self.exitcodes: List[int] | None = None
        self.startretries: int | None = None
        self.starttime: int | None = None
        self.stopsignal: ProgramConfig.Signal | None = None
        self.stoptime: int | None = None
        self.stdout: str | None = None
        self.stderr: str | None = None
        self.user: str | None = None
        self.env: Dict[str, str] | None = None
        self.__dict__.update(config)

    def __iter__(self) -> Any:
        return iter(self.__dict__.items())


class Program:
    """
    Represents a program that can be managed by the service.
    """

    def __init__(
        self,
        **config: Dict[str, Any],
    ) -> None:
        """
        Initializes a new instance of the Program class.

        Args:
            **config: The configuration parameters for the program.
        """
        self._config = ProgramConfig(**config)

    def __str__(self) -> str:
        return f"Program(name={self._config.name}, command={self._config.cmd}, numprocs={self._config.numprocs})"

    def __repr__(self) -> str:
        return f"Program(name={self._config.name}, command={self._config.cmd}, numprocs={self._config.numprocs})"

    @property
    def config(self) -> ProgramConfig:
        """
        Gets the configuration parameters for the program.

        Returns:
            The configuration parameters as a dictionary.
        """
        return self._config

    @config.setter
    def config(self, config: Dict[Any, Any]) -> ProgramConfig:
        """
        Sets the configuration parameters for the program.

        Args:
            config: The new configuration parameters as a dictionary.
        """
        self._config = ProgramConfig(**config)
        return self.config

    def start(self) -> None:
        """
        Starts the program.
        """

        if self._config.cmd:
            subprocess.Popen(self._config.cmd.split(), cwd=self._config.workingdir)

    def stop(self) -> None:
        """
        Stops the program.
        """
        pass

    def restart(self) -> None:
        """
        Restarts the program.
        """
        pass

    def reload(self) -> None:
        """
        Reloads the configuration of the program.
        """
        pass


class Service:
    """
    Represents a service that manages programs and their configurations.
    """

    def __init__(
        self,
        **config: Dict[Any, Any],
    ) -> None:
        """
        Initializes a new instance of the Service class.

        Args:
            **config: The configuration parameters for the service.
        """
        self._config: ServiceConfig = ServiceConfig(**config)
        self._programs: List[Program] = []

    def status(self):
        """
        Displays the status of all programs.
        """
        pass

    def start(self, program_names: Optional[List[str]] = None):
        """
        Starts one or multiple programs.

        Args:
            program_names: The name of the programs to start.
        """
        for program in self._programs:
            if program_names and program.config.name in program_names:
                program.start()

    def stop(self, program_names: Optional[List[str]] = None):
        """
        Stops one or multiple programs.

        Args:
            program_names: The name of the programs to stop.
        """
        for program in self._programs:
            if program_names and program.config.name in program_names:
                program.stop()

    def restart(self, program_names: Optional[List[str]] = None):
        """
        Restarts one or multiple programs.

        Args:
            program_names: The name of the programs to restart.
        """
        for program in self._programs:
            if program_names and program.config.name in program_names:
                program.restart()

    @property
    def config(self) -> ServiceConfig:
        """
        Gets the configuration parameters for the service.

        Returns:
            The configuration parameters.
        """
        return self._config

    @config.setter
    def config(self, config: Dict[Any, Any]) -> ServiceConfig:
        """
        Sets the configuration parameters for the service.

        Args:
            config: The new configuration parameters as a dictionary.

        Returns:
            The configuration parameters.
        """
        self._config = ServiceConfig(**config)
        return self.config

    def reload(self, program_names: Optional[List[str]] = None) -> None:
        """
        Reloads the configuration of one or multiple programs.
        """
        for program in self._programs:
            if program_names and program.config.name in program_names:
                program.reload()
