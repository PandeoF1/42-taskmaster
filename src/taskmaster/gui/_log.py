from ..utils.log_reader import LogReader
import curses
from ..utils.logger import logger
import time


def log(self, log: LogReader = None) -> None:
    try:
        if "log" not in self.win:
            self.win["log"] = curses.newwin(self.height, self.width, 0, 0)
            self.win_data["log"] = dict()
            self.win_data["log"]["selected"] = "log"
            self.win_data["log"]["index_x"] = 0
            self.win_data["log"]["index_y"] = 0
            self.win_data["log"]["LogReader"] = None
        if log is None:
            log = self.win_data["log"]["LogReader"]
        else:
            self.win_data["log"]["LogReader"] = log
        self.win_active = "log"
        self.win["log"].addstr(3, 4, "Taskmaster - Log")
        log.size = self.height - 8
        content = log.lines
        # Clear the window
        for i in range(self.height - 8):
            self.win["log"].addstr(4 + i, 4, " " * (self.width - 6))
        self.win_data["log"]["content_height"] = len(content)
        self.win_data["log"]["content_width"] = 0
        for line in content:
            self.win_data["log"]["content_width"] = max(
                self.win_data["log"]["content_width"], len(line)
            )
        for i, line in enumerate(content):
            # print only from index to window width (start the print from x: 4 and y: 5, index are only where to start in the table)
            if (
                i >= self.win_data["log"]["index_y"]
                and i < self.height - 8 + self.win_data["log"]["index_y"]
            ):
                self.win["log"].addstr(
                    4 + i - self.win_data["log"]["index_y"],
                    4,
                    line[
                        self.win_data["log"]["index_x"] : self.win_data["log"][
                            "index_x"
                        ]
                        + self.width
                        - 8
                    ],
                )
        if (
            self.win_data["log"]["index_x"] - 8 + self.width
            < self.win_data["log"]["content_width"] - 8
        ):
            # print ">" for each line
            for i in range(self.height - 8):
                self.win["log"].addstr(
                    4 + i,
                    self.width - 4,
                    ">",
                    curses.A_REVERSE,
                )
        if self.win_data["log"]["index_x"] > 0:
            # print "<" for each line
            for i in range(self.height - 8):
                self.win["log"].addstr(
                    4 + i,
                    3,
                    "<",
                    curses.A_REVERSE,
                )
        else:
            for i in range(self.height - 8):
                self.win["log"].addstr(
                    4 + i,
                    3,
                    " ",
                )
        self.win["log"].addstr(
            self.height - 3,
            4,
            f"Press 'q' to go back. - (↑•↓•←•→ to navigate) {log._start}",
        )
        self.box("log")

        self.win["log"].refresh()
    except curses.error as e:
        logger.error(f"Failed to load log page. {e}")


def log_nav(self, key: int) -> None:
    # Navigate through the log
    try:
        # logger.debug(f"[Log] Key pressed: {key}")
        if self.win_active != "log":
            return 0
        if key == 113:  # q
            self.win_data["log"]["index_y"] = 0
            self.win_data["log"]["index_x"] = 0
            self.services()
            return 0
        if key == 65:  # ↑
            self.win_data["log"]["LogReader"].down()
        if key == 66:  # ↓
            self.win_data["log"]["LogReader"].up()
        if key == 68:  # ←
            if self.win_data["log"]["index_x"] > 0:
                self.win_data["log"]["index_x"] -= 2
        if key == 67:  # →
            if (
                self.win_data["log"]["index_x"]
                < self.win_data["log"]["content_width"] - self.width + 8
            ):
                self.win_data["log"]["index_x"] += 2
        self.log()
    except curses.error as e:
        logger.error(f"[Log] Failed to navigate. {e}")


def log_not_found(self, path: str) -> None:
    # Log not found page
    try:
        # logger.debug("Loading log not found page.")
        if "log_not_found" not in self.win:
            self.win["log_not_found"] = curses.newwin(self.height, self.width, 0, 0)
            self.win_data["log_not_found"] = dict()
            self.win_data["log_not_found"]["selected"] = "log_not_found"
        self.win_active = "log_not_found"
        self.box("log_not_found")
        self.win["log_not_found"].addstr(3, 4, "Taskmaster - Log not found")
        self.win["log_not_found"].addstr(
            int(self.height / 2),
            int(self.width / 2 - 31),
            f"The log file `{path}` could not be found.",
        )
        count = 6
        while count > 1:
            count -= 1
            self.win["log_not_found"].addstr(
                self.height - 3,
                4,
                f"Automatically closing in {count} second{'s.' if count > 1 else '. '}",
            )
            self.win["log_not_found"].refresh()
            time.sleep(1)
        self.services()
    except curses.error as e:
        logger.error(f"Failed to load log not found page. {e}")
