import curses
import asyncio
import signal
import argparse
from .utils.email import Email
from typing import Any

from .service import ServiceHandler

from .utils.logger import logger
from .gui.gui import Gui
from .utils.config import Config, generate_config

need_reload = False
need_exit = False


def signal_handler(sig: Any, frame: Any) -> None:
    logger.warning("CTRL+C detected. Exiting...")
    global need_exit
    need_exit = True


def reload_config(sig: Any, frame: Any) -> None:
    logger.info("Reloading configuration. (SIGHUP)")
    global need_reload
    need_reload = True


def init_signal() -> None:
    logger.info("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, reload_config)


async def interfaces(stdscr, config) -> None:
    logger.info("Starting taskmaster.")
    global need_reload, need_exit
    try:
        if config.email:
            email = Email(config)
            asyncio.create_task(email.send("hello", "Taskmaster started."))
        else:
            email = None
        interface = Gui()
        interface.service_handler = ServiceHandler(
            email=email,
            **dict({"services": config.services})
        )
        task = asyncio.create_task(interface.service_handler.autostart())
        interface.config = config
        interface.default()
        while True:
            await asyncio.sleep(0.01)
            interface.update_size()
            key = interface.win[interface.win_active].getch()
            stop = interface.default_nav(key)
            if stop == -1 or need_exit:
                break
            elif stop:
                continue
            elif interface.services_nav(key) == -1:
                break
            elif interface.config_nav(key) == -1:
                break
            elif interface.log_nav(key) == -1:
                break
            if need_reload or interface.need_reload:
                need_reload = False
                interface.need_reload = False
                config = Config(config.path)
                if config.email:
                    email = Email(config)
                interface.service_handler.config = dict({"services": config.services})
                asyncio.create_task(interface.service_handler.reload(email=email))
                interface.config = config
                interface.configuration_success()
                interface.default()
        interface.services_destroy()
        await interface.service_handler.delete()
        await asyncio.sleep(2)
        interface.end()
        task.cancel()
    except Exception as e:
        logger.error(e)


async def taskmaster(config: Config) -> None:
    logger.info("Starting taskmaster.")
    init_signal()
    await asyncio.gather(curses.wrapper(interfaces, config))


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--file", help="Path to the configuration file")
        parser.add_argument("-g", "--generate", help="Generate a configuration file at path", type=str)
        parser.add_argument(
            "-l",
            "--loglevel",
            default="warning",
            help="Provide logging level. Example --loglevel debug, default=warning",
        )
        args = parser.parse_args()
        if args.generate:
            generate_config(args.generate)
            return
        config = Config(args.file if args.file else "taskmaster.yml")
    except Exception as e:
        interface = Gui()
        interface.configuration_error(e)
        return
    logger.setLevel(args.loglevel.upper())
    asyncio.run(taskmaster(config))


if __name__ == "__main__":
    main()
