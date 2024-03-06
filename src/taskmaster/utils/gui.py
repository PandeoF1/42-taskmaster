import curses
from .logger import logger
import sys


class Gui:
    """
    A class that creates a GUI for the taskmaster application.
    """

    pages = ["services", "wip"]

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
            if self.height < 20 or self.width < 80:
                logger.error("Screen is too small.")
                self.end()
                sys.exit(1)
            curses.start_color()
            curses.use_default_colors()
            self.win = dict()
            self.win_data = dict()
            self.default()
        except:
            logger.error("Failed to initialize screen.")

    def box(self, windows) -> None:
        # Create a window with a box around it
        try:
            logger.debug("Loading box.")
            self.win[windows].box(0, 0)
            self.win[windows].addstr(0, 2, " " + windows + " ")
            self.win[windows].refresh()
            # self.win[windows].nodelay(True) # non-blocking getch
        except:
            logger.error("Failed to load box.")

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
        except:
            logger.error("Failed to load default page.")

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
                return 0
            self.default()
        except:
            logger.error("[Default] Failed to navigate.")
            return 0

    def services_nav(self, key: int) -> None:
        try:
            logger.debug(f"[Services] Key pressed: {key}")
            if key == 113:  # q
                self.default()
                return
            self.services()
        except:
            logger.error("[Services] Failed to navigate.")

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
        except:
            logger.error("Failed to load services page.")

    def configuration(self) -> None:
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
            # Print "no configaration file provided"
            self.win["configuration"].addstr(
                self.height / 2, self.width / 2 - 31, "No configuration file provided."
            )
            self.win["configuration"].refresh()
        except:
            # log.log("Failed to load configuration page.", level="ERROR")
            self.end()

    def end(self) -> None:
        # Restore terminal settings and end curses mode
        try:
            self.stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
        except:
            logger.error("Failed to end screen.")

    def __del__(self) -> None:
        self.end()
