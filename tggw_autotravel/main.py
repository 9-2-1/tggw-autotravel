import logging
import time

from .getch import GetchMSVCRT, getch_context
from .run import RunWinConsole, run_context
from .tui import TUIColorama, tui_context

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
    with getch_context(GetchMSVCRT()) as getch:
        with tui_context(TUIColorama(lines=38, columns=92)) as tui:
            with run_context(
                RunWinConsole(
                    "cmd.exe",
                    "/c",
                    "The Ground Gives Way.exe",
                    lines=38,
                    columns=92,
                    cwd="tggw_game",  # profile-directory
                )
            ) as run:
                while run.alive():
                    while True:
                        char = getch.getch()
                        if char == "":
                            break
                        log.debug(f"char: {char!r}")
                        # handle
                        # with errorcatcher(log):
                        run.write(char)
                    run.read_screen()
                    tui.screen = run.screen
                    tui.refresh()
                    time.sleep(CYCLE_TIME)
                log.info("Not alive")
