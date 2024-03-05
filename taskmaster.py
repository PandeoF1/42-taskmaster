#!/usr/bin/env python3
import curses
import sys
import signal
import time
from utils.logger import logger
from utils.gui import gui

log = logger("taskmaster")

#Handle ctrl c
def signal_handler(sig, frame):
    log.log("CTRL+C detected. Exiting...", level="WARNING")
    log.close()
    sys.exit(0)

def init_signal():
    log.log("Initializing signal handler.")
    signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    try:
        log.log("Starting taskmaster.")
        init_signal()
        interface = gui()
        interface.default()
        while True:
            log.log(interface.win_active)
            if interface.win_active == 'default' and interface.default_nav(interface.win['default'].getch()) == -1:
                break
            if interface.win_active == 'services' and interface.services_nav(interface.win['services'].getch()) == -1:
                break
        interface.end()
    except Exception as e:
        log.log(f"An error occurred: {e}", level="ERROR")
        log.close()
        sys.exit(1)