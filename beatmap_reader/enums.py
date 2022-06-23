from enum import IntEnum, Enum


class Countdown(IntEnum):
    NONE = 0
    NORMAL = 1
    HALF = 2
    DOUBLE = 3


class SampleSet(Enum):
    DEFAULT = "Default"
    NORMAL = "Normal"
    SOFT = "Soft"
    DRUM = "Drum"


class GameMode(IntEnum):
    STANDARD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


class OverlayPosition(Enum):
    NOCHANGE = "NoChange"
    BELOW = "Below"
    ABOVE = "Above"
