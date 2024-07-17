
from enum import Enum

class Orientation(Enum):
    PORTRAIT = 1
    LANDSCAPE = 2

    @staticmethod
    def from_string(s):
        try:
            return Orientation[s.upper()]
        except KeyError:
            raise ValueError(f"Unknown orientation: {s}")

    def __str__(self):
        return self.value