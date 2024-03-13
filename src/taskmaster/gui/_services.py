import curses
from .table import table
from ..utils.logger import logger
from ..utils.log_reader import LogReader


def services(self) -> None:
    # Services page
    try:
        # logger.debug("Loading services page.")
        if "services" not in self.win:
            self.win["services"] = curses.newwin(self.height, self.width, 0, 0)
            self.win_data["services"] = dict()
            self.win_data["services"]["selected"] = "service"
            self.win_data["services"]["index_x"] = 0
            self.win_data["services"]["index_y"] = 0
            self.win_data["services"]["selected_line"] = 0
        self.win_active = "services"
        self.box("services")
        self.win["services"].addstr(3, 4, "Taskmaster - Services")
        content = table(self.config.services)
        # Clear the window
        for i in range(self.height - 8):
            self.win["services"].addstr(4 + i, 4, " " * (self.width - 6))
        split_content = content.split("\n")
        self.win_data["services"]["content_height"] = len(split_content)
        self.win_data["services"]["content_width"] = 0
        for line in split_content:
            if len(line) > self.win_data["services"]["content_width"]:
                self.win_data["services"]["content_width"] = len(line)
        for i, line in enumerate(split_content):
            # print only from index to window width (start the print from x: 4 and y: 5, index are only where to start in the table)
            if (
                i >= self.win_data["services"]["index_y"]
                and i < self.height - 8 + self.win_data["services"]["index_y"]
            ):
                if not i == 0:
                    self.win["services"].addstr(
                        4 + i - self.win_data["services"]["index_y"],
                        4,
                        line[
                            self.win_data["services"]["index_x"] : self.win_data[
                                "services"
                            ]["index_x"]
                            + self.width
                            - 8
                        ],
                        (
                            curses.A_REVERSE
                            if self.win_data["services"]["selected_line"] + 1 == i
                            else 0
                        ),
                    )
        self.win["services"].addstr(
            4,
            4,
            split_content[0][
                self.win_data["services"]["index_x"] : self.win_data["services"][
                    "index_x"
                ]
                + self.width
                - 8
            ],
            curses.A_UNDERLINE,
        )
        if self.win_data["services"]["index_x"] - 8 + self.width < len(content[0]) - 8:
            # print ">" for each line
            for i in range(self.height - 8):
                self.win["services"].addstr(
                    4 + i,
                    self.width - 4,
                    ">",
                    curses.A_REVERSE,
                )
        if self.win_data["services"]["index_x"] > 0:
            # print "<" for each line
            for i in range(self.height - 8):
                self.win["services"].addstr(
                    4 + i,
                    3,
                    "<",
                    curses.A_REVERSE,
                )
        else:
            for i in range(self.height - 8):
                self.win["services"].addstr(
                    4 + i,
                    3,
                    " ",
                )
        self.win["services"].addstr(
            self.height - 3,
            4,
            "Press 'q' to go back. - (↑•↓•←•→ to navigate, e to open stderr, o to open stdout)",
        )
        self.win["services"].refresh()
    except curses.error as e:
        logger.error(f"Failed to load services page. {e}")


def services_nav(self, key: int) -> None:
    try:
        # logger.debug(f"[Services] Key pressed: {key}")
        if self.win_active != "services":
            return 0
        if key == 113:  # q
            self.default()
            self.win_data["services"]["index_y"] = 0
            self.win_data["services"]["index_x"] = 0
            self.win_data["services"]["selected_line"] = 0
            return
        if key == 65:  # ↑``
            if self.win_data["services"]["selected_line"] > 0:
                self.win_data["services"]["selected_line"] -= 1
                if (
                    self.win_data["services"]["selected_line"]
                    < self.win_data["services"]["index_y"]
                ):
                    self.win_data["services"]["index_y"] -= 1
        if key == 66:  # ↓
            # increment self.win_data["services"]["selected_line"] if it's not the last line
            if (
                self.win_data["services"]["content_height"]
                > self.win_data["services"]["selected_line"]
                and self.win_data["services"]["selected_line"] + 2
                < self.win_data["services"]["content_height"] - 1
            ):
                self.win_data["services"]["selected_line"] += 1
                if (
                    self.win_data["services"]["selected_line"] + 2
                    > self.height - 8 + self.win_data["services"]["index_y"]
                ):
                    self.win_data["services"]["index_y"] += 1
        if key == 68:  # ←
            if self.win_data["services"]["index_x"] > 0:
                self.win_data["services"]["index_x"] -= 2
        if key == 67:  # →
            if (
                self.win_data["services"]["index_x"]
                < self.win_data["services"]["content_width"] - self.width + 8
            ):
                self.win_data["services"]["index_x"] += 2
        try:
            if key == 10:  # Enter
                # logger.info(
                #    f"Selected service: {self.win_data['services']['selected_line']} {self.config.services[self.win_data['services']['selected_line']]['name']} {self.config.services[self.win_data['services']['selected_line']]['stdout']}"
                # )
                self.log(
                    LogReader(
                        log_file=self.config.services[
                            self.win_data["services"]["selected_line"]
                        ]["stdout"]
                    )
                )
                return
            if key == 101:  # e -> stderr
                self.log(
                    LogReader(
                        log_file=self.config.services[
                            self.win_data["services"]["selected_line"]
                        ]["stderr"]
                    )
                )
                return
            if key == 111:  # o -> open stdout
                self.log(
                    LogReader(
                        log_file=self.config.services[
                            self.win_data["services"]["selected_line"]
                        ]["stdout"]
                    )
                )
                return
        except FileNotFoundError as e:
            self.log_not_found(e.filename)
            return
        self.services()
    except curses.error as e:
        logger.error(f"[Services] Failed to navigate. {e}")
