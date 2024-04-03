import curses
from ..utils.logger import logger
import time


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
            while self.height < 20 or self.width < 90:
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
            elif self.win_active == "log":
                self.log()
            else:
                self.default()
    except curses.error as e:
        logger.error(f"Failed to update screen size. {e}")


def clear(self, window) -> None:
    # Clear the window
    try:
        # logger.debug(f"Clearing window: {window}")
        self.win[window].clear()
        self.win[window].refresh()
    except curses.error as e:
        logger.error(f"Failed to clear window. {e}")


def box(self, windows) -> None:
    # Create a window with a box around it
    try:
        # logger.debug("Loading box.")
        self.win[windows].box(0, 0)
        self.win[windows].addstr(0, 2, " " + windows + " ")
        self.win[windows].refresh()
        self.win[windows].nodelay(True)  # non-blocking getch
    except curses.error as e:
        logger.error(f"Failed to load box. {e}")
