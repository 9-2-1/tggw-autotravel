import sqlite3
from typing import Any


def selectmap() -> Any:
    with glob.glob("nerimap-*.txt") as filename:
        with open(filename, "r") as file:
            mapdata = file.read()
    pass


def readdata() -> None:
    pass


def writedata() -> Any:
    pass
