from typing import Generator, Any, List
from contextlib import contextmanager
import datetime
import traceback


def log(*args: List[Any]) -> None:
    with open("error.log", "a", encoding="utf-8") as err_file:
        print(f"{datetime.datetime.now()}", file=err_file)
        print(*args, file=err_file)


@contextmanager
def errorlog() -> Generator[None, None, None]:
    try:
        yield
    except Exception:
        with open("error.log", "a", encoding="utf-8") as err_file:
            print(f"{datetime.datetime.now()}", file=err_file)
            traceback.print_exc(file=err_file)
