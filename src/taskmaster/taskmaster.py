import curses
import asyncio
import sys
import signal
import time
from typing import Any

from .utils.logger import logger
from .utils.gui import Gui
from .utils.config import Config

# log = logger("taskmaster")


# Handle ctrl c
def signal_handler(sig: Any, frame: Any) -> None:
    # logger.log("CTRL+C detected. Exiting...", level="WARNING")
    # logger.close()
    sys.exit(0)


def init_signal() -> None:
    # logger.log("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)


async def interfaces(config) -> None:
    # logger.log("Starting taskmaster.")
    try:
        interface = Gui()
        interface.config = config
        interface.default()
        while True:
            interface.update_size()
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
            elif (
                interface.win_active == "configuration"
                and interface.config_nav(key) == -1
            ):
                break
        # Stop all services
        interface.end()
    except Exception as e:
        logger.error(e)


async def taskmaster(config: Config) -> None:
    logger.info("Starting taskmaster.")
    init_signal()
    event_loop = asyncio.get_event_loop()
    tasks = [
        event_loop.create_task(interfaces(config)),
    ]
    await asyncio.gather(*tasks)
    # logger.close()


async def services(config: Config) -> None:
    pass


def main() -> None:
    try:
        config = Config()
    except Exception as e:
        interface = Gui()
        interface.configuration_error(e)
        return
    asyncio.run(taskmaster(config))


if __name__ == "__main__":
    main()
