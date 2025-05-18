from abc import abstractmethod
from contextlib import contextmanager
from typing import Generator

from ..screen import Screen


class TUIBase:
    screen: Screen

    @abstractmethod
    def __init__(self) -> None: ...

    @abstractmethod
    def refresh(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


@contextmanager
def tui_context(self: TUIBase) -> Generator[TUIBase, None, None]:
    try:
        yield self
    finally:
        self.close()
