from enum import Enum


class MasteryLevel(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    MASTERED = "MASTERED"


class QuestionType(str, Enum):
    SINGLE_MCQ = "SINGLE_MCQ"
    MULTI_MCQ = "MULTI_MCQ"
    NUMERICAL = "NUMERICAL"
    TRUE_FALSE = "TRUE_FALSE"
    SUBJECTIVE = "SUBJECTIVE"


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class MistakeType(str, Enum):
    CONCEPTUAL = "CONCEPTUAL"
    SILLY = "SILLY"
    CALCULATION = "CALCULATION"
    MISREAD = "MISREAD"
    TIME_PRESSURE = "TIME_PRESSURE"
    OTHER = "OTHER"


class RevisionEventType(str, Enum):
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    SKIPPED = "SKIPPED"
    RESCHEDULED = "RESCHEDULED"


class QualityRating(str, Enum):
    AGAIN = "AGAIN"
    HARD = "HARD"
    GOOD = "GOOD"
    EASY = "EASY"
