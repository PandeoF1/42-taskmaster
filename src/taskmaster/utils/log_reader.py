from .logger import LOG_FILE


class LogReader:
    """
    LogReader class for reading log files and managing the buffer.

    Args:
        log_file (str): The path to the log file. Default is LOG_FILE.
        log_level (str): The log level. Default is "DEBUG".
        size (int): The size of the buffer. Default is 20.

    Attributes:
        size (int): The size of the buffer.
        end (bool): Whether the end of the file has been reached.

    Methods:
        up: Moves the buffer up by one line.
        down: Moves the buffer down by one line.
        lines: Returns the lines in the buffer.
        latest: Places the start of the buffer at the end of the file.
    """

    def __init__(
        self,
        log_file: str = LOG_FILE,
        log_level: str = "DEBUG",
        size: int = 20,
    ) -> None:
        self._log_file = open(log_file, "r")
        self._log_level = log_level
        self._start = 0
        self._stay_end = False

        if size <= 0:
            raise ValueError("Size must be greater than 0.")
        self._size = size

        self._buffer = []
        self.latest()

    def __del__(self) -> None:
        if hasattr(self, "_log_file"):
            self._log_file.close()

    def _read(self) -> list[str]:
        """
        Reads the file and appends new lines to the buffer.

        Returns:
            list[str]: The lines read from the file.

        """
        new_lines = self._log_file.readlines()
        self._buffer.extend(new_lines)

        end = (
            self._start + self._size
            if self._start + self._size < len(self._buffer)
            else len(self._buffer)
        )

        return self._buffer[self._start : end]

    @property
    def size(self) -> int:
        """
        Getter for the size attribute.

        Returns:
            int: The size of the buffer.

        """
        return self._size

    @size.setter
    def size(self, size: int) -> int:
        """
        Setter for the size attribute.

        Args:
            size (int): The new size of the buffer.

        Returns:
            The new size of the buffer.

        """
        if size <= 0:
            raise ValueError("Size must be greater than 0.")
        self._start -= size - self._size if self._start - size + self._size >= 0 else 0
        self._size = size
        return self._size

    def up(self) -> int:
        """
        Moves the buffer up by one line.

        Returns:
            int: The new starting index of the buffer.

        """
        if self.end:
            self.stay_end = True
        else:
            self.stay_end = False
        self._read()
        if self._start + self._size < len(self._buffer):
            self._start += 1
        return self._start

    def down(self) -> int:
        """
        Moves the buffer down by one line.

        Returns:
            int: The new starting index of the buffer.

        """
        self.stay_end = False
        self._read()
        if self._start > 0:
            self._start -= 1
        return self._start

    @property
    def end(self) -> bool:
        """
        Returns whether the end of the file has been reached or not.

        Returns:
            bool: True if the end of the file has been reached, False otherwise.

        """
        self._read()
        return self._start + self._size >= len(self._buffer)

    @property
    def lines(self) -> list[str]:
        """
        Returns the lines in the buffer.

        Returns:
            list[str]: The lines in the buffer.

        """
        if self._stay_end:
            self.latest()
        return self._read()

    @property
    def stay_end(self) -> bool:
        """
        Returns whether the buffer is at the end of the file or not.

        Returns:
            bool: True if the buffer is at the end of the file, False otherwise.

        """
        return self._stay_end

    @stay_end.setter
    def stay_end(self, value: bool) -> None:
        """
        Setter for the stay_end attribute.

        Args:
            value (bool): The new value for the stay_end attribute.

        Returns:
            None

        """
        self._stay_end = value

    def latest(self) -> None:
        """
        Places the start of the buffer at the end of the file.

        Returns:
            None

        """
        self.stay_end = True
        self._read()
        self._start = len(self._buffer) - self._size
