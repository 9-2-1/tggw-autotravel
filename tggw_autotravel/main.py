import logging
import time

from .controller import Controller

log = logging.getLogger(__name__)

CYCLE_TIME = 0.01


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        filename="main.log",
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )
    log.info("Start")
    maingame = Controller(38, 92)
    maingame.run()
    while maingame.is_running():
        while True:
            char = maingame.getch()
            if char == "":
                break
            log.debug(f"char: {char!r}")
            # handle
            # with errorcatcher(log):
            maingame.write(char)
        maingame.nextframe()
        time.sleep(CYCLE_TIME)
    maingame.stop()
