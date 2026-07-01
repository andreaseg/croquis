import os
import pytest

from croquis.util import (
    parse_timer,
    scale_rect_to_bounds,
    resolve_image_path,
    shorten_to_location,
    images_in_path,
)


@pytest.mark.parametrize(
    "timers,expected",
    [
        ("30s", [30]),
        ("2m", [120]),
        ("30s 30s 1m", [30, 30, 60]),
        ("3*30s", [30, 30, 30]),
        ("2*2m", [120, 120]),
        ("10s*3", [10, 10, 10]),
        ("2*10s 2m*3 10m", [10, 10, 120, 120, 120, 600]),
    ],
)
def test_parse_timer(timers: str, expected: list[int]):
    assert parse_timer(timers) == expected


@pytest.mark.parametrize(
    "rect, bounds, expected_rect",
    [
        ((400, 300), (400, 300), (400, 300)),
        ((300, 400), (300, 400), (300, 400)),
        ((200, 100), (100, 50), (100, 50)),
        ((200, 100), (100, 100), (100, 50)),
        ((100, 200), (100, 100), (50, 100)),
    ],
)
def test_scale_rect_to_bounds(
    rect: tuple[int, int], bounds: tuple[int, int], expected_rect: tuple[int, int]
):
    scale = scale_rect_to_bounds(rect, bounds)
    assert (int(rect[0] * scale), int(rect[1] * scale)) == expected_rect


def test_resolve_image_path_finds_via_configured_location(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "library" / "Hands").mkdir(parents=True)

    resolved = resolve_image_path("Hands", ["library"])

    assert os.path.isdir(resolved)
    assert os.path.abspath(resolved) == str(tmp_path / "library" / "Hands")


def test_resolve_image_path_falls_back_to_raw_path_when_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    resolved = resolve_image_path("nonexistent", ["also-nonexistent"])

    assert resolved == "nonexistent"


def test_images_in_path_finds_files_via_configured_location(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "library" / "Hands"
    folder.mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"")
    (folder / "b.jpg").write_bytes(b"")

    images = images_in_path(["Hands"], ["library"])

    assert len(images) == 2


def test_images_in_path_still_finds_files_via_legacy_cwd_relative_path(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "images" / "Hands"
    folder.mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"")

    images = images_in_path(["images/Hands"])

    assert len(images) == 1


def test_shorten_to_location_shortens_contained_path(tmp_path):
    location = tmp_path / "library"
    folder = location / "Hands"
    folder.mkdir(parents=True)

    shortened = shorten_to_location(str(folder), [str(location)])

    assert shortened == "Hands"


def test_shorten_to_location_picks_shortest_of_multiple_matches(tmp_path):
    outer = tmp_path / "outer"
    inner = outer / "library"
    folder = inner / "Hands"
    folder.mkdir(parents=True)

    shortened = shorten_to_location(str(folder), [str(outer), str(inner)])

    assert shortened == "Hands"


def test_shorten_to_location_falls_back_when_not_contained(tmp_path):
    unrelated = tmp_path / "elsewhere"
    unrelated.mkdir()
    folder = tmp_path / "library" / "Hands"
    folder.mkdir(parents=True)

    shortened = shorten_to_location(str(folder), [str(unrelated)])

    assert shortened == str(folder)
