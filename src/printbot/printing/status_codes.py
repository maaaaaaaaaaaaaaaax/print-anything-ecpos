from typing import Final

from printbot.printing.ports import PaperState

QUERY_ONLINE: Final = b"\x10\x04\x01"
QUERY_OFFLINE_CAUSE: Final = b"\x10\x04\x02"
QUERY_PAPER: Final = b"\x10\x04\x04"

OFFLINE_BIT: Final = 0x08
COVER_OPEN_BIT: Final = 0x04
PAPER_ADEQUATE_BITS: Final = 0x12
PAPER_NEAR_END_BITS: Final = 0x1E
PAPER_OUT_BITS: Final = 0x72


def parse_online(reply: bytes) -> bool | None:
    if not reply:
        return None
    return not reply[0] & OFFLINE_BIT


def parse_cover_open(reply: bytes) -> bool | None:
    if not reply:
        return None
    return bool(reply[0] & COVER_OPEN_BIT)


def parse_paper(reply: bytes) -> PaperState:
    if not reply:
        return PaperState.UNKNOWN
    byte = reply[0]
    if byte & PAPER_OUT_BITS == PAPER_OUT_BITS:
        return PaperState.OUT
    if byte & PAPER_NEAR_END_BITS == PAPER_NEAR_END_BITS:
        return PaperState.NEAR_END
    if byte & PAPER_ADEQUATE_BITS == PAPER_ADEQUATE_BITS:
        return PaperState.OK
    return PaperState.UNKNOWN
