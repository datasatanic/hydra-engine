from enum import Enum


class IndexStatus(int, Enum):
    EMPTY = 0,
    READ_FROM_DISK = 1,
    CREATED = 2,
    NEED_TO_UNSTASH = 3,
    UNSTASH_FAILED = 4
