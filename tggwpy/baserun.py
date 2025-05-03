from abc import abstractmethod
from typing import Dict, List, Optional

from . import screen


class Baserun:
    """
    The original game runner
    """

    lines: int
    columns: int
    screen: screen.Screen

    @abstractmethod
    def __init__(
        self,
        command: List[str],
        lines: int,
        columns: int,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None: ...

    @abstractmethod
    def update_screen(self) -> bool:
        """
        Apply new pty updates to screen.Screen
        Return true if there are new updates
        """
        ...

    @abstractmethod
    def sendtext(self, text: str) -> None: ...

    @abstractmethod
    def sendkey(self, key_code: int, modifiers: int) -> None: ...

    @abstractmethod
    def is_running(self) -> bool: ...

    @abstractmethod
    def terminate(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
