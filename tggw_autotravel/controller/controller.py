import logging
from typing import Optional

from .base import ControllerBase
from ..screen import Screen

from ..getch import GetchMSVCRT
from ..run import RunBase, RunWinPTY
from ..tui import TUIColorama

log = logging.getLogger(__name__)

CYCLE_TIME = 0.01


class Controller(ControllerBase):
    def __init__(self, lines: int, columns: int) -> None:
        self.screen = Screen(lines, columns)
        self.game: Optional[RunBase] = None
        self.getcher = GetchMSVCRT()
        self.tui = TUIColorama(lines=lines, columns=columns)

    def run(self) -> None:
        """
        Start the game program
        """
        if self.game is not None:
            raise RuntimeError("Game already running")
        self.game = RunWinPTY(
            "cmd.exe",
            "/c",
            "The Ground Gives Way.exe",
            lines=self.screen.lines,
            columns=self.screen.columns,
            cwd="tggw_game",  # profile-directory
        )

    def is_running(self) -> bool:
        """
        Check if the game program is running
        """
        return self.game is not None and self.game.alive()

    def stop(self) -> None:
        """
        Stop the game program
        """
        if self.game is None:
            return
        self.game.close()
        self.game = None

    def nextframe(self) -> None:
        """
        Wait for next frame of game
        """
        if self.game is None:
            #
            self.screen = Screen.from_json("")
            return
        self.game.read_screen()
        self.screen = self.game.screen
        self.tui.screen = self.screen
        self.tui.refresh()

    def write(self, text: str) -> None:
        """
        Write text to the game program
        """
        if self.game is None:
            raise RuntimeError("Game not running")
        self.game.write(text)

    def getch(self) -> str:
        """
        Get user input
        """

        return self.getcher.getch()
