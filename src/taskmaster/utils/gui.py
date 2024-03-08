import curses
from .logger import logger
import time


# Generate table
def config_table(data):
    # Get the keys (column names) from the first row of data
    keys = []
    # Get all the keys of all the services
    for service in data:
        for key in service.keys():
            if key not in keys:
                keys.append(key)

    padding = 3

    # Calculate the maximum width for each column
    max_widths = [len(key) for key in keys]
    for row in data:
        for i, value in enumerate(row.values()):
            max_widths[i] = max(max_widths[i], len(str(value)))

    content = ""
    # Print the header
    for i, key in enumerate(keys):
        content += f"{key:<{max_widths[i] + padding}}".capitalize()
    content += "\n"
    # Print the data
    for row in data:
        for i, value in enumerate(row.values()):
            content += f"{str(value):<{max_widths[i] + padding}}"
        content += "\n"
    return content


class Gui:
    """
    A class that creates a GUI for the taskmaster application.
    """

    pages = ["services", "config"]

    def __init__(self):
        # Initialize the screen
        logger.debug("Initializing screen.")
        try:
            self.stdscr = curses.initscr()
            self.stdscr.keypad(True)
            self.stdscr.clear()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            self.height, self.width = self.stdscr.getmaxyx()
            logger.debug(f"Screen size: {self.height}x{self.width}")
            while self.height < 20 or self.width < 80:
                self.screen_too_small()
                time.sleep(0.1)
                self.height, self.width = self.stdscr.getmaxyx()
            curses.start_color()
            curses.use_default_colors()
            self.win = dict()
            self.win_data = dict()
            self.default()
        except curses.error as e:
            logger.error(f"Failed to initialize screen. {e}")

    def screen_too_small(self) -> None:
        # Print an error message if the screen is too small
        try:
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, "Screen is too small.")
            self.stdscr.refresh()
        except curses.error as e:
            logger.error(f"Failed to print error message. {e}")

    def update_size(self) -> None:
        # Update the window size
        try:
            if (self.height, self.width) != self.stdscr.getmaxyx():
                self.height, self.width = self.stdscr.getmaxyx()
                while self.height < 20 or self.width < 80:
                    self.screen_too_small()
                    time.sleep(0.1)
                    self.height, self.width = self.stdscr.getmaxyx()
                logger.debug(f"Screen size: {self.height}x{self.width}")
                for window in self.win:
                    self.win[window].resize(self.height, self.width)
                    self.clear(window)
                if self.win_active == "default":
                    self.default()
                elif self.win_active == "services":
                    self.services()
                elif self.win_active == "configuration":
                    self.configuration()
                else:
                    self.default()
        except curses.error as e:
            logger.error(f"Failed to update screen size. {e}")

    def clear(self, window) -> None:
        # Clear the window
        try:
            logger.debug(f"Clearing window: {window}")
            self.win[window].clear()
            self.win[window].refresh()
        except curses.error as e:
            logger.error(f"Failed to clear window. {e}")

    def box(self, windows) -> None:
        # Create a window with a box around it
        try:
            logger.debug("Loading box.")
            self.win[windows].box(0, 0)
            self.win[windows].addstr(0, 2, " " + windows + " ")
            self.win[windows].refresh()
            # self.win[windows].nodelay(True) # non-blocking getch
        except curses.error as e:
            logger.error(f"Failed to load box. {e}")

    def default(self) -> None:
        # Default page
        try:
            logger.debug("Loading default page.")
            if "default" not in self.win:
                self.win["default"] = curses.newwin(self.height, self.width, 0, 0)
                self.win_data["default"] = dict()
                self.win_data["default"]["selected"] = self.pages[0]
            self.win_active = "default"
            self.box("default")
            self.win["default"].addstr(3, 4, "Taskmaster - Main menu")
            for i, page in enumerate(self.pages):
                if page == self.win_data["default"]["selected"]:
                    self.win["default"].addstr(
                        5 + i, 6, f"{i + 1}. {page.capitalize()}", curses.A_REVERSE
                    )
                else:
                    self.win["default"].addstr(
                        5 + i, 6, f"{i + 1}. {page.capitalize()}"
                    )
            self.win["default"].addstr(
                self.height - 3, 4, "Press 'q' to quit. - (↑•↓ to navigate)"
            )
            self.win["default"].refresh()
        except curses.error as e:
            logger.error(f"Failed to load default page. {e}")

    def default_nav(self, key: int) -> int:
        # Navigate through the pages
        try:
            logger.debug(f"[Default] Key pressed: {key}")
            if key == 113:  # q
                return -1
            elif key == 66:  # ↓
                # select next in the list
                index = self.pages.index(self.win_data["default"]["selected"])
                if index < len(self.pages) - 1:
                    index += 1
                    self.win_data["default"]["selected"] = self.pages[index]
            elif key == 65:  # ↑
                # select previous in the list
                index = self.pages.index(self.win_data["default"]["selected"])
                if index > 0:
                    index -= 1
                    self.win_data["default"]["selected"] = self.pages[index]
            elif key == 10:  # Enter
                # Open the selected page
                if self.win_data["default"]["selected"] == "services":
                    self.services()
                if self.win_data["default"]["selected"] == "config":
                    self.configuration()
                return 0
            self.default()
        except curses.error as e:
            logger.error(f"[Default] Failed to navigate. {e}")
            return 0

    def services_nav(self, key: int) -> None:
        try:
            logger.debug(f"[Services] Key pressed: {key}")
            if key == 113:  # q
                self.default()
                return
            self.services()
        except curses.error as e:
            logger.error(f"[Services] Failed to navigate. {e}")

    def services(self) -> None:
        # Services page
        try:
            logger.debug("Loading services page.")
            if "services" not in self.win:
                self.win["services"] = curses.newwin(self.height, self.width, 0, 0)
                self.win_data["services"] = dict()
                self.win_data["services"]["selected"] = "service1"
            self.win_active = "services"
            self.box("services")
            self.win["services"].addstr(3, 4, "Taskmaster - Services")
            self.win["services"].addstr(
                self.height - 3, 4, "Press 'q' to go back. - (↑•↓ to navigate)"
            )

            # | name | status | pid | uptime | restarts | exit code
            self.win["services"].addstr(5, 4, "Name", curses.A_UNDERLINE)
            self.win["services"].addstr(5, 15, "Status", curses.A_UNDERLINE)
            self.win["services"].addstr(5, 25, "PID", curses.A_UNDERLINE)
            self.win["services"].addstr(5, 35, "Uptime", curses.A_UNDERLINE)
            self.win["services"].addstr(5, 45, "Restarts", curses.A_UNDERLINE)
            self.win["services"].addstr(5, 55, "Exit code", curses.A_UNDERLINE)

            self.win["services"].refresh()
        except curses.error as e:
            logger.error(f"Failed to load services page. {e}")

    def configuration(self) -> None:
        # Configuration page
        try:
            logger.debug("Loading configuration page.")
            if "configuration" not in self.win:
                self.win["configuration"] = curses.newwin(self.height, self.width, 0, 0)
                self.win_data["configuration"] = dict()
                self.win_data["configuration"]["selected"] = "config1"
                self._config_index = {"x": 0, "y": 0}
            self.win_active = "configuration"
            self.box("configuration")
            self.win["configuration"].addstr(3, 4, "Taskmaster - Configuration")

            services = self.config.services
            content = config_table(services)

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
                    i >= self._config_index["y"]
                    and i < self.height - 8 + self._config_index["y"]
                ):
                    if not i == 0:
                        self.win["configuration"].addstr(
                            4 + i - self._config_index["y"],
                            4,
                            line[
                                self._config_index["x"]:self._config_index["x"]
                                + self.width
                                - 8
                            ],
                        )
            self.win["configuration"].addstr(
                4,
                4,
                split_content[0][
                    self._config_index["x"]:self._config_index["x"] + self.width - 8
                ],
                curses.A_UNDERLINE,
            )
            if (
                self._config_index["x"] - 8 + self.width
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
            if self._config_index["x"] > 0:
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
            logger.debug(f"[Configuration] Key pressed: {key}")
            if key == 113:  # q
                self._config_index = {"x": 0, "y": 0}
                self.default()
                return
            if key == 65:  # ↑
                if self._config_index["y"] > 0:
                    self._config_index["y"] -= 1
            if key == 66:  # ↓
                if (
                    self._config_index["y"]
                    < self.win_data["configuration"]["content_height"] - self.height + 7
                ):
                    self._config_index["y"] += 1
            if key == 68:  # ←
                if self._config_index["x"] > 0:
                    self._config_index["x"] -= 2
            if key == 67:  # →
                if (
                    self._config_index["x"]
                    < self.win_data["configuration"]["content_width"] - self.width
                ):
                    self._config_index["x"] += 2
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
                self.win_data["configuration"]["selected"] = "config1"
            self.win_active = "configuration"
            self.box("configuration")
            self.win["configuration"].addstr(3, 4, "Taskmaster - Configuration")
            # Print error
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

    def end(self) -> None:
        # Restore terminal settings and end curses mode
        try:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
        except curses.error as e:
            logger.error(f"Failed to end screen. {e}")

    def __del__(self) -> None:
        self.end()
