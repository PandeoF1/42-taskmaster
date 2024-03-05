#!/usr/bin/env python3
import sys
import signal
import time
from utils.logger import logger

main_log = logger("my_app")

#Handle ctrl c
def signal_handler(sig, frame):
    main_log.log("This is an informational message.")
    main_log.log("This is a warning message.", level="WARNING")
    main_log.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    time.sleep(10)