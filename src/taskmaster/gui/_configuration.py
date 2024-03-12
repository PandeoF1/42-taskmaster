import curses
from .table import table
from ..utils.logger import logger
import time


def configuration(self) -> None:
    # Configuration page
    try:
        # logger.debug("Loading configuration page.")
        if "configuration" not in self.win:
            self.win["configuration"] = curses.newwin(self.height, self.width, 0, 0)
            self.win_data["configuration"] = dict()
            self.win_data["configuration"]["selected"] = "config"
            self.win_data["configuration"]["index_x"] = 0
            self.win_data["configuration"]["index_y"] = 0
        self.win_active = "configuration"
        self.box("configuration")
        self.win["configuration"].addstr(3, 4, "Taskmaster - Configuration")
        services = self.config.services
        content = table(services)
        split_content = content.split("\n")
        self.win_data["configuration"]["content_height"] = len(split_content)
        self.win_data["configuration"]["content_width"] = 0
        for line in split_content:
            if len(line) > self.win_data["configuration"]["content_width"]:
                self.win_data["configuration"]["content_width"] = len(line)
        # Clear the window
        for i in range(self.height - 8):
            self.win["configuration"].addstr(4 + i, 4, " " * (self.width - 6))
        for i, line in enumerate(split_content):
            # print only from index to window width (start the print from x: 4 and y: 5, index are only where to start in the table)
            if (
                i >= self.win_data["configuration"]["index_y"]
                and i < self.height - 8 + self.win_data["configuration"]["index_y"]
            ):
                if not i == 0:
                    self.win["configuration"].addstr(
                        4 + i - self.win_data["configuration"]["index_y"],
                        4,
                        line[
                            self.win_data["configuration"]["index_x"] : self.win_data[
                                "configuration"
                            ]["index_x"]
                            + self.width
                            - 8
                        ],
                    )
        self.win["configuration"].addstr(
            4,
            4,
            split_content[0][
                self.win_data["configuration"]["index_x"] : self.win_data[
                    "configuration"
                ]["index_x"]
                + self.width
                - 8
            ],
            curses.A_UNDERLINE,
        )
        if (
            self.win_data["configuration"]["index_x"] - 8 + self.width
            < self.win_data["configuration"]["content_width"] - 8
        ):
            # print ">" for each line
            for i in range(self.height - 8):
                self.win["configuration"].addstr(
                    4 + i,
                    self.width - 4,
                    ">",
                    curses.A_REVERSE,
                )
        if self.win_data["configuration"]["index_x"] > 0:
            # print "<" for each line
            for i in range(self.height - 8):
                self.win["configuration"].addstr(
                    4 + i,
                    3,
                    "<",
                    curses.A_REVERSE,
                )
        else:
            for i in range(self.height - 8):
                self.win["configuration"].addstr(
                    4 + i,
                    3,
                    " ",
                )
        self.win["configuration"].addstr(
            self.height - 3, 4, "Press 'q' to go back. - (↑•↓•←•→ to navigate)"
        )
        self.win["configuration"].refresh()
    except curses.error as e:
        logger.error(f"Failed to load configuration page. {e}")


def config_nav(self, key: int) -> None:
    try:
        # logger.debug(f"[Configuration] Key pressed: {key}")
        if self.win_active != "configuration":
            return 0
        if key == 113:  # q
            self.win_data["configuration"]["index_y"] = 0
            self.win_data["configuration"]["index_x"] = 0
            self.default()
            return
        if key == 65:  # ↑``
            if self.win_data["configuration"]["index_y"] > 0:
                self.win_data["configuration"]["index_y"] -= 1
        if key == 66:  # ↓
            if (
                self.win_data["configuration"]["index_y"]
                < self.win_data["configuration"]["content_height"] - self.height + 7
            ):
                self.win_data["configuration"]["index_y"] += 1
        if key == 68:  # ←
            if self.win_data["configuration"]["index_x"] > 0:
                self.win_data["configuration"]["index_x"] -= 2
        if key == 67:  # →
            if (
                self.win_data["configuration"]["index_x"]
                < self.win_data["configuration"]["content_width"] - self.width + 7
            ):
                self.win_data["configuration"]["index_x"] += 2
        self.configuration()
    except curses.error as e:
        logger.error(f"[Configuration] Failed to navigate. {e}")


def configuration_error(self, error) -> None:
    # Configuration page
    try:
        # log.log("Loading configuration page.")
        if "configuration" not in self.win:
            self.win["configuration"] = curses.newwin(self.height, self.width, 0, 0)
            self.win_data["configuration"] = dict()
            self.win_data["configuration"]["selected"] = "config"
        self.win_active = "configuration"
        self.box("configuration")
        self.win["configuration"].addstr(3, 4, "Taskmaster - Configuration")
        self.win["configuration"].addstr(
            int(self.height / 2), int(self.width / 2 - 31), f"Error: {error}"
        )
        count = 6
        while count > 1:
            count -= 1
            self.win["configuration"].addstr(
                self.height - 3,
                4,
                f"Automatically closing in {count} second{'s.' if count > 1 else '. '}",
            )
            self.win["configuration"].refresh()
            time.sleep(1)
        self.win["configuration"].refresh()
    except curses.error as e:
        logger.error(
            f"Failed to load configuration page. {e}",
        )
