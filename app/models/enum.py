from enum import Enum


class MasteryLevel(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    MASTERED = "MASTERED"
