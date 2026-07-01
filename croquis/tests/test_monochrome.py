import pytest
from PIL import Image

from croquis.monochrome import apply_monochrome
from croquis.constants import LUMA_WEIGHTS


def _luminance(rgb: tuple[int, int, int]) -> float:
    r_weight, g_weight, b_weight = LUMA_WEIGHTS
    r, g, b = rgb
    return r_weight * r + g_weight * g + b_weight * b


def _solid_color_pixel(color: tuple[int, int, int]) -> tuple[int, int, int]:
    image = Image.new("RGB", (2, 2), color=color)
    result = apply_monochrome(image)
    assert result.size == image.size
    assert result.mode == "RGB"
    return result.getpixel((0, 0))


def test_black_stays_black():
    assert _solid_color_pixel((0, 0, 0)) == (0, 0, 0)


def test_white_becomes_warm_sepia():
    r, g, b = _solid_color_pixel((255, 255, 255))
    assert r >= g >= b
    assert r > b, "highlights should show a clear warm sepia bias"


def test_dark_grey_stays_close_to_neutral():
    r, g, b = _solid_color_pixel((40, 40, 40))
    assert max(r, g, b) - min(r, g, b) <= 3, "shadows should stay near-neutral"


def test_bright_values_are_more_tinted_than_dark_values():
    dark_r, dark_g, dark_b = _solid_color_pixel((40, 40, 40))
    bright_r, bright_g, bright_b = _solid_color_pixel((220, 220, 220))
    dark_spread = max(dark_r, dark_g, dark_b) - min(dark_r, dark_g, dark_b)
    bright_spread = max(bright_r, bright_g, bright_b) - min(bright_r, bright_g, bright_b)
    assert bright_spread > dark_spread


@pytest.mark.parametrize(
    "color", [(0, 0, 0), (60, 60, 60), (128, 128, 128), (180, 180, 180), (200, 200, 200)]
)
def test_perceptual_luminance_is_preserved_below_clipping_range(
    color: tuple[int, int, int],
):
    input_luma = _luminance(color)
    output_luma = _luminance(_solid_color_pixel(color))
    assert abs(output_luma - input_luma) < 1.5


def test_colour_input_is_converted_via_perceptual_luma_not_naive_average():
    # A saturated green reads much brighter than a saturated blue to the eye,
    # even though a plain per-channel average would treat them as equal.
    green_luma = _luminance(_solid_color_pixel((0, 255, 0)))
    blue_luma = _luminance(_solid_color_pixel((0, 0, 255)))
    assert green_luma > blue_luma
