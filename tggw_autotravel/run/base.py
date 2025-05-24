from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, Dict, Generator

from ..screen import Screen


class RunBase(ABC):
    @abstractmethod
    def __init__(
        self,
        cmd: str,
        *args: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        lines: int = 24,
        columns: int = 80,
    ) -> None: ...

    screen: Screen

    @abstractmethod
    def alive(self) -> bool:
        """
        Return True if the program is alive, False otherwise
        """
        ...

    @abstractmethod
    def read_screen(self) -> None:
        """
        Call this to read the output of program to update the screen buffer.
        For example:
        ```
        program.read_screen()
        state_char = program.screen.buffer[0][0]
        ```
        """
        ...

    @abstractmethod
    def write(self, text: str) -> None:
        """
        Write to the stdin of program
        """
        ...

    @abstractmethod
    def kill(self) -> None:
        """
        Kill the program
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Close the connection
        """
        ...


@contextmanager
def run_context(self: RunBase) -> Generator[RunBase, None, None]:
    try:
        yield self
    finally:
        self.close()
