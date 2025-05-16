from abc import abstractmethod
from contextlib import contextmanager
from typing import Generator


class GetchBase:
    @abstractmethod
    def __init__(self) -> None: ...
    @abstractmethod
    def getch(self) -> str: ...
    @abstractmethod
    def close(self) -> None: ...


@contextmanager
def getch_context(self: GetchBase) -> Generator[GetchBase, None, None]:
    try:
        yield self
    finally:
        self.close()
