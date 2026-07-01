import re
import toml

from dataclasses import dataclass, asdict, field
from typing import Iterable
from .util import parse_bool, format_time, sort_tags
from .constants import DEFAULT_KEYBINDINGS
from .i18n import translate

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

    def get_label(self, language: str = "en") -> tuple[str, str, str]:
        if self.manual:
            return (
                translate("Manual", language),
                translate("Click to go to next image", language),
                "∞",
            )
        if self.timers:
            s = sum(croquis.util.parse_timer(self.timers))

            timers = self.timers.strip()
            timers = re.sub(r"\s+", ", ", timers)
            timers = " ".join([t if "*" in t else f"1*{t}" for t in timers.split(" ")])
            timers = timers.replace("*", "×")

            return translate("Timed", language), timers, format_time(s)

        raise ValueError("Mode must be manual or have timers set")


@dataclass
class Config:
    dimensions: str
    imageset: dict[str, ImageSet]
    mode: dict[str, Mode]
    category: dict[str, Category]
    image_locations: list[str] = field(default_factory=list)
    keybindings: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_KEYBINDINGS))
    excluded_images: list[str] = field(default_factory=list)
    zen_mode: bool = False
    theme: str = "auto"
    language: str = "en"
    monochrome_default: bool = False

    def __post_init__(self):
        self.imageset = {k: ImageSet(**v) for (k, v) in self.imageset.items()}
        self.mode = {k: Mode(**v) for (k, v) in self.mode.items()}
        self.category = {k: Category(**v) for (k, v) in self.category.items()}

    def tags(self) -> list[str]:
        return sort_tags({tag for imageset in self.imageset.values() for tag in imageset.tags})


def imagesets_matching_category(
    imagesets: dict[str, ImageSet], category: Category
) -> dict[str, ImageSet]:
    return {
        name: imageset
        for name, imageset in imagesets.items()
        if set(category.tags).issubset(set(imageset.tags))
    }


def merge_imagesets(imagesets: Iterable[ImageSet]) -> ImageSet:
    imagesets = list(imagesets)
    tags = {tag for imageset in imagesets for tag in imageset.tags}
    paths = {path for imageset in imagesets for path in imageset.paths}
    return ImageSet(tags=list(tags), paths=list(paths))


def load_config(path: str) -> Config:
    with open(path, mode="r") as f:
        return Config(**toml.loads(f.read()))


def save_config(config: Config, path: str) -> None:
    with open(path, mode="w") as f:
        toml.dump(asdict(config), f)


def replace_config_fields(target: Config, source: Config) -> None:
    target.__dict__.update(source.__dict__)
