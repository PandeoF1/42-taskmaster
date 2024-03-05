#!/usr/bin/env python3
import curses
import asyncio
import sys
import signal
import time
from utils.logger import logger
from utils.gui import gui

log = logger("taskmaster")

#Handle ctrl c
def signal_handler(sig, frame):
    # log.log("CTRL+C detected. Exiting...", level="WARNING")
    log.close()
    sys.exit(0)

def init_signal():
    # log.log("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)

async def interfaces():
    try:
        # log.log("Starting taskmaster.")
        interface = gui()
        interface.default()
        while True:
            key = interface.win[interface.win_active].getch()
            while key == curses.ERR:
                time.sleep(0.01)
                key = interface.win[interface.win_active].getch()
            if interface.win_active == 'default' and interface.default_nav(key) == -1:
                break
            elif interface.win_active == 'services' and interface.services_nav(key) == -1:
                break
        interface.end()
    except Exception as e:
        # log.log(f"An error occurred: {e}", level="ERROR")
        log.close()
        sys.exit(1)

async def main():
    init_signal()
    event_loop = asyncio.get_event_loop()
    tasks = [
        event_loop.create_task(interfaces()),
    ]
    await asyncio.gather(*tasks)
    log.close()

if __name__ == "__main__":
    asyncio.run(main())
