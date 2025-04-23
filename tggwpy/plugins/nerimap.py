import sqlite3
import glob
from typing import Any


def selectmap() -> Any:
    for filename in glob.glob("nerimap-*.txt"):
        with open(filename, "r") as file:
            mapdata = file.read()
    pass


def readdata() -> None:
    pass


def writedata() -> Any:
    pass
