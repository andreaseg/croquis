import re

from dataclasses import dataclass
from .util import parse_bool, format_time, sort_tags

import croquis.util

@dataclass
class Category:
    tags: list[str]

@dataclass
class ImageSet:
    tags: list[str]
    paths: list[str]


@dataclass
class Mode:
    timers: str = ""
    default: bool = False
    manual: bool = False

    def __post_init__(self):
        self.default = parse_bool(self.default)
        self.manual = parse_bool(self.manual)

    def get_label(self) -> tuple[str, str, str]:
        if self.manual:
            return "Manual", "Click to go to next image", "∞"
        if self.timers:
            s = sum(croquis.util.parse_timer(self.timers))

            timers = self.timers.strip()
            timers = re.sub(r"\s+", ", ", timers)
            timers = " ".join([t if "*" in t else f"1*{t}" for t in timers.split(" ")])
            timers = timers.replace("*", "×")

            return "Timed", timers, format_time(s)


@dataclass
class Config:
    dimensions: str
    imageset: dict[str, ImageSet]
    mode: dict[str, Mode]
    category: dict[str, Category]

    def __post_init__(self):
        self.imageset = {k: ImageSet(**v) for (k, v) in self.imageset.items()}
        self.mode = {k: Mode(**v) for (k, v) in self.mode.items()}
        self.category = {k: Category(**v) for (k, v) in self.category.items()}

    def tags(self) -> list[str]:
        return sort_tags({tag for imageset in self.imageset.values() for tag in imageset.tags})
