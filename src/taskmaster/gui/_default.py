import curses
from ..utils.logger import logger


def default(self) -> None:
    # Default page
    try:
        # logger.debug("Loading default page.")
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
                self.win["default"].addstr(5 + i, 6, f"{i + 1}. {page.capitalize()}")
        self.win["default"].addstr(
            self.height - 3, 4, "Press 'q' to quit. - (↑•↓ to navigate)"
        )
        self.win["default"].refresh()
    except curses.error as e:
        logger.error(f"Failed to load default page. {e}")


def default_nav(self, key: int) -> int:
    # Navigate through the pages
    try:
        # logger.debug(f"[Default] Key pressed: {key}")
        if self.win_active != "default":
            return 0
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
            elif self.win_data["default"]["selected"] == "config":
                self.configuration()
            return True
        self.default()
    except curses.error as e:
        logger.error(f"[Default] Failed to navigate. {e}")
        return 0
