import curses
import asyncio
import sys
import signal
import argparse
from typing import Any
import random

from .utils.logger import logger
from .gui.gui import Gui
from .utils.config import Config, generate_config

# log = logger("taskmaster")


# Handle ctrl c
def signal_handler(sig: Any, frame: Any) -> None:
    logger.warning("CTRL+C detected. Exiting...")
    # Do this properly
    sys.exit(0)


def init_signal() -> None:
    # logger.log("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)


async def interfaces(stdscr, config) -> None:
    # logger.log("Starting taskmaster.")
    try:
        interface = Gui()
        interface.config = config
        interface.default()
        while True:
            await asyncio.sleep(0.01)
            interface.update_size()
            key = interface.win[interface.win_active].getch()
            stop = interface.default_nav(key)
            if stop == -1:
                break
            elif stop:
                continue
            elif interface.services_nav(key) == -1:
                break
            elif interface.config_nav(key) == -1:
                break
            elif interface.log_nav(key) == -1:
                break
        # Stop all services
        interface.end()
    except Exception as e:
        logger.error(e)


async def test(config: Config) -> None:
    while True:
        # logger.info("test")
        # edit config
        config.services[0]["numprocs"] = random.randint(1, 100)
        await asyncio.sleep(0.5)


async def taskmaster(config: Config) -> None:
    logger.info("Starting taskmaster.")
    init_signal()
    # Execute interfaces and test in parallel
    await asyncio.gather(curses.wrapper(interfaces, config), test(config))
    # logger.close()


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--file", help="Path to the configuration file")
        parser.add_argument("-g", "--generate", help="Generate a configuration file at path", type=str)
        args = parser.parse_args()
        if args.generate:
            generate_config(args.generate)
            return
        config = Config(args.file if args.file else "taskmaster.yml")
    except Exception as e:
        interface = Gui()
        interface.configuration_error(e)
        return
    asyncio.run(taskmaster(config))


if __name__ == "__main__":
    main()
