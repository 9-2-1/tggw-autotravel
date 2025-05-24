from abc import abstractmethod
from ..screen import Screen


class ControllerBase:
    screen: Screen

    @abstractmethod
    def run(self) -> None:
        """
        Start the game program
        """
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the game program is running
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the game program
        """
        ...

    @abstractmethod
    def nextframe(self) -> None:
        """
        Wait for next frame of game
        """
        ...

    @abstractmethod
    def write(self, text: str) -> None:
        """
        Write text to the game program
        """
        ...

    @abstractmethod
    def getch(self) -> str:
        """
        Get user input
        """
        ...
