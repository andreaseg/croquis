from PIL import Image

from croquis.constants import LUMA_WEIGHTS, SEPIA_REFERENCE_COLOR, MONOCHROME_TINT_STRENGTH


def _luminance(rgb: tuple[float, float, float]) -> float:
    r_weight, g_weight, b_weight = LUMA_WEIGHTS
    r, g, b = rgb
    return r_weight * r + g_weight * g + b_weight * b


def _sepia_ratios() -> tuple[float, float, float]:
    reference_luminance = _luminance(SEPIA_REFERENCE_COLOR)
    return tuple(channel / reference_luminance for channel in SEPIA_REFERENCE_COLOR)


def _channel_lut(ratio: float, tint_strength: float) -> list[int]:
    lut = []
    for luma in range(256):
        strength = tint_strength * (luma / 255)
        value = luma * (1 + strength * (ratio - 1))
        lut.append(max(0, min(255, round(value))))
    return lut


def _build_luts(tint_strength: float) -> tuple[list[int], list[int], list[int]]:
    r_ratio, g_ratio, b_ratio = _sepia_ratios()
    return (
        _channel_lut(r_ratio, tint_strength),
        _channel_lut(g_ratio, tint_strength),
        _channel_lut(b_ratio, tint_strength),
    )


_LUT_R, _LUT_G, _LUT_B = _build_luts(MONOCHROME_TINT_STRENGTH)


def apply_monochrome(image: Image.Image) -> Image.Image:
    """Perceptual greyscale with a slight sepia tint that grows with brightness.

    Shadows stay neutral (grey/black), highlights pick up warmth - a look
    similar to graphite on paper. The tint is constructed so the output's own
    perceptual luminance always matches the input's greyscale value; see
    SEPIA_REFERENCE_COLOR/MONOCHROME_TINT_STRENGTH in constants.py to adjust.
    """
    grey = image.convert("L")
    r = grey.point(_LUT_R)
    g = grey.point(_LUT_G)
    b = grey.point(_LUT_B)
    return Image.merge("RGB", (r, g, b))
