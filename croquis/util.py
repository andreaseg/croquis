import os
import random
import re
import sys
import copy
from typing import Iterable
import tkinter as tk
from tkinter import font as tkFont


def parse_bool(s: str | bool) -> bool:
    if isinstance(s, bool):
        return s
    elif s.casefold() == "true":
        return True
    elif s.casefold() == "false":
        return False
    else:
        raise ValueError(f"Invalid boolean value {s}")


def scale_rect_to_bounds(rect: tuple[int, int], bounds: tuple[int, int]) -> float:
    return min(bounds[0] / float(rect[0]), bounds[1] / float(rect[1]))


def generate_random_image_sequence(
    paths: list[str],
    timers: str,
    locations: Iterable[str] = (),
    excluded: Iterable[str] = (),
) -> list[tuple[str, int, bool]]:
    potential_images = images_in_path(paths, locations, excluded)
    if not potential_images:
        raise Exception("No images found for the selected image set(s).")

    timers = parse_timer(timers)

    sampled_images = _sample_with_repeats(potential_images, len(timers))
    is_mirrored = [bool(random.getrandbits(1)) for _ in range(len(timers))]

    return list(zip(sampled_images, timers, is_mirrored))


def _sample_with_repeats(pool: list[str], count: int) -> list[str]:
    """Sample `count` items from `pool` without repeats until the pool is
    exhausted, then reshuffle and continue - so a pool smaller than `count`
    fills the rest by repeating images rather than raising."""
    result = []
    while len(result) < count:
        remaining = count - len(result)
        result.extend(random.sample(pool, min(remaining, len(pool))))
    return result


def resolve_image_path(path: str, locations: Iterable[str]) -> str:
    for location in locations:
        candidate = os.path.join(location, path)
        if os.path.isdir(candidate):
            return candidate
    return path


def normalize_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def shorten_to_location(path: str, locations: Iterable[str]) -> str:
    abs_path = os.path.abspath(path)
    candidates = [path]
    for location in [".", *locations]:
        try:
            rel = os.path.relpath(abs_path, os.path.abspath(location))
        except ValueError:
            continue
        if not rel.startswith(".."):
            candidates.append(rel)
    return min(candidates, key=len)


def images_in_path(
    paths: list[str], locations: Iterable[str] = (), excluded: Iterable[str] = ()
) -> list[str]:
    search_locations = [".", *locations]
    excluded_normalized = {normalize_path(path) for path in excluded}
    images = []
    for path in paths:
        resolved = resolve_image_path(path, search_locations)
        for dirpath, _dirnames, filenames in os.walk(resolved):
            for filename in filenames:
                candidate = os.path.join(dirpath, filename)
                if normalize_path(candidate) not in excluded_normalized:
                    images.append(candidate)
    return images


def parse_timer(timers: str) -> list[int]:
    seconds_per_unit = {"s": 1, "m": 60}

    is_time_re = re.compile(r"\d+[msMS]")
    is_numer_re = re.compile(r"\d+")

    re.sub(r"\s+", "", timers)

    def is_time(s):
        return is_time_re.match(s)

    def is_number(s):
        return is_numer_re.match(s)

    def parse_timer_expr(e):
        return int(e[:-1]) * seconds_per_unit[e[-1]]

    timer = []
    for t in timers.split(" "):
        if "*" in t:
            l, r = t.split("*")
            if is_time(l) and is_number(r):
                time_expr = l
                count = r
            elif is_number(l) and is_time(r):
                count = l
                time_expr = r
            else:
                raise Exception(f"'{t}' is not a valid time expression")
        else:
            time_expr = t
            count = 1
            if not is_time(t):
                raise Exception(f"'{t}' is not a valid time expression")

        timer.extend([parse_timer_expr(time_expr)] * int(count))

    return timer


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class RichText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_font = tkFont.nametofont(self.cget("font"))

        em = default_font.measure("m")
        default_size = default_font.cget("size")
        bold_font = tkFont.Font(**default_font.configure())
        italic_font = tkFont.Font(**default_font.configure())
        h1_font = tkFont.Font(**default_font.configure())

        bold_font.configure(weight="bold")
        italic_font.configure(slant="italic")
        h1_font.configure(size=int(default_size * 2), weight="bold")

        self.tag_configure("bold", font=bold_font)
        self.tag_configure("italic", font=italic_font)
        self.tag_configure("h1", font=h1_font, spacing3=default_size)

        lmargin2 = em + default_font.measure("\u2022 ")
        self.tag_configure("bullet", lmargin1=em, lmargin2=lmargin2)

    def insert_bullet(self, index, text):
        self.insert(index, f"\u2022 {text}", "bullet")


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        width,
        height,
        cornerradius,
        padding,
        color,
        border_color,
        border,
        bg,
        text,
        font,
        command=None,
    ):
        tk.Canvas.__init__(
            self, parent, borderwidth=0, relief="flat", highlightthickness=0, bg=bg
        )
        self.command = command

        if cornerradius > 0.5 * width:
            print("Error: cornerradius is greater than width.")
            return None

        if cornerradius > 0.5 * height:
            print("Error: cornerradius is greater than height.")
            return None

        rad = 2 * cornerradius

        self.create_polygon(
            (
                padding,
                height - cornerradius - padding,
                padding,
                cornerradius + padding,
                padding + cornerradius,
                padding,
                width - padding - cornerradius,
                padding,
                width - padding,
                cornerradius + padding,
                width - padding,
                height - cornerradius - padding,
                width - padding - cornerradius,
                height - padding,
                padding + cornerradius,
                height - padding,
            ),
            fill=color,
            outline=border_color,
            width=border,
        )
        self.create_arc(
            (padding, padding + rad, padding + rad, padding),
            start=90,
            extent=90,
            fill=color,
            outline=color,
        )
        self.create_arc(
            (width - padding - rad, padding, width - padding, padding + rad),
            start=0,
            extent=90,
            fill=color,
            outline=color,
        )
        self.create_arc(
            (
                width - padding,
                height - rad - padding,
                width - padding - rad,
                height - padding,
            ),
            start=270,
            extent=90,
            fill=color,
            outline=color,
        )
        self.create_arc(
            (padding, height - padding - rad, padding + rad, height - padding),
            start=180,
            extent=90,
            fill=color,
            outline=color,
        )

        self.create_arc(
            (padding, padding + rad, padding + rad, padding),
            start=90,
            extent=90,
            style="arc",
            outline=border_color,
            width=border,
        )
        self.create_arc(
            (width - padding - rad, padding, width - padding, padding + rad),
            start=0,
            extent=90,
            style="arc",
            outline=border_color,
            width=border,
        )
        self.create_arc(
            (
                width - padding,
                height - rad - padding,
                width - padding - rad,
                height - padding,
            ),
            start=270,
            extent=90,
            style="arc",
            outline=border_color,
            width=border,
        )
        self.create_arc(
            (padding, height - padding - rad, padding + rad, height - padding),
            start=180,
            extent=90,
            style="arc",
            outline=border_color,
            width=border,
        )

        self.create_text(width / 2, height / 2, text=text, font=font, anchor="center")

        (x0, y0, x1, y1) = self.bbox("all")
        width = x1 - x0
        height = y1 - y0
        self.configure(width=width, height=height)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        self.configure(relief="sunken")

    def _on_release(self, event):
        self.configure(relief="raised")
        if self.command is not None:
            self.command()


def format_time(s: int) -> str:
    h = int(s / 3600)
    m = int(s % 3600 / 60)
    s = s % 60
    t = []
    if h:
        t.append(f"{h}h")
    if m:
        t.append(f"{m}m")
    if s:
        t.append(f"{s}s")
    if not t:
        t = ["0s"]
    return " ".join(t)

def sort_tags(tags: Iterable[str]) -> list[str]:
    priority = [
        "male",
        "female",
        "mixed",
        "unknown",
        "portrait",
        "figure"
        ]
    
    sorted_tags = []
    tags = list(copy.copy(tags))

    for item in priority:
        if item in tags:
            sorted_tags.append(item)
            tags.remove(item)
    
    sorted_tags.extend(tags)
    return sorted_tags