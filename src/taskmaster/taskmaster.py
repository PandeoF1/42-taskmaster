import curses
import asyncio
import sys
import signal
import time
from typing import Any

from .utils.logger import logger
from .utils.gui import Gui

# log = logger("taskmaster")


# Handle ctrl c
def signal_handler(sig: Any, frame: Any) -> None:
    # logger.log("CTRL+C detected. Exiting...", level="WARNING")
    # logger.close()
    sys.exit(0)


def init_signal() -> None:
    # logger.log("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)


async def interfaces() -> None:
    try:
        # logger.log("Starting taskmaster.")
        interface = Gui()
        interface.default()
        while True:
            key = interface.win[interface.win_active].getch()
            while key == curses.ERR:
                time.sleep(0.01)
                key = interface.win[interface.win_active].getch()
            if interface.win_active == "default" and interface.default_nav(key) == -1:
                break
            elif (
                interface.win_active == "services" and interface.services_nav(key) == -1
            ):
                break
        # Stop all services
        interface.end()
    except Exception as e:
        # logger.log(f"An error occurred: {e}", level="ERROR")
        # logger.close()
        sys.exit(1)


async def taskmaster() -> None:
    logger.info("Starting taskmaster.")
    init_signal()
    event_loop = asyncio.get_event_loop()
    tasks = [
        event_loop.create_task(interfaces()),
    ]
    await asyncio.gather(*tasks)
    # logger.close()


def main() -> None:
    asyncio.run(taskmaster())


if __name__ == "__main__":
    main()
