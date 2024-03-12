import curses
from ..utils.logger import logger
from ..utils.log_reader import LogReader
import time
from .table import table


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
            while self.height < 20 or self.width < 90:
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

    from ._utils import screen_too_small, update_size, clear, box
    from ._default import default, default_nav
    from ._services import services, services_nav
    from ._log import log, log_nav, log_not_found
    from ._configuration import configuration, config_nav, configuration_error

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
