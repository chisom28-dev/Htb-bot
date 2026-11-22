
import logging
import signal
import time
from pathlib import Path

running = True

logging.basicConfig(
    filename=Path(__file__).with_name("engine.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def shutdown(signum, frame):
    global running
    logging.info("Engine shutdown requested.")
    running = False

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

logging.info("HTG Scalper simulation engine started.")

try:
    while running:
        logging.info("Engine heartbeat: running.")
        time.sleep(5)
finally:
    logging.info("HTG Scalper simulation engine stopped.")
