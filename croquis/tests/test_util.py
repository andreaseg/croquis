import pytest

from croquis.util import parse_timer, scale_rect_to_bounds


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
