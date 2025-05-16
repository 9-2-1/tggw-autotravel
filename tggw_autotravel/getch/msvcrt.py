import msvcrt
import logging
from codecs import getincrementaldecoder

from .base import GetchBase

log = logging.getLogger(__name__)


class GetchMSVCRT(GetchBase):
    def __init__(self) -> None:
        self.decoder = getincrementaldecoder("utf-8")(errors="ignore")

    def getch(self) -> str:
        if msvcrt.kbhit():
            read = msvcrt.getch()
            readt = self.decoder.decode(read)
            log.debug(f"Read: {read!r} -> {readt!r}")
            return readt
        else:
            return ""

    def close(self) -> None:
        pass
