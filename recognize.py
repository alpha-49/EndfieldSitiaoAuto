from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


PROJECT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PROJECT_DIR / "markers"
FEATURE_SIZE = (12, 16)
EXPECTED_LABELS = frozenset(
    {"0"}
    | {f"{number}{suit}" for number in range(1, 6) for suit in ("m", "p", "s")}
)


def _load_templates() -> tuple[tuple[str, Image.Image], ...]:
    templates: list[tuple[str, Image.Image]] = []

    for path in sorted(TEMPLATE_DIR.glob("*.png")):
        label = path.stem
        with Image.open(path) as image:
            feature = image.convert("RGB").resize(
                FEATURE_SIZE, Image.Resampling.BOX
            )
        templates.append((label, feature))

    loaded_labels = {label for label, _ in templates}
    missing = EXPECTED_LABELS - loaded_labels
    if missing:
        raise RuntimeError(f"Missing marker templates: {sorted(missing)}")
    if len(templates) != len(EXPECTED_LABELS):
        raise RuntimeError(
            "Marker template directory must contain exactly the 16 expected files."
        )

    return tuple(templates)


_TEMPLATES = _load_templates()


def _classify_marker(marker: Image.Image) -> str:
    feature = marker.convert("RGB").resize(FEATURE_SIZE, Image.Resampling.BOX)
    best_label = ""
    best_score = float("inf")

    for label, template in _TEMPLATES:
        difference = ImageChops.difference(feature, template)
        red, green, blue = ImageStat.Stat(difference).rms
        score = red * red + green * green + blue * blue
        if score < best_score:
            best_score = score
            best_label = label

    return best_label


def recognize(markers: Sequence[Image.Image]) -> str:
    """Classify five marker crops and return their concatenated labels."""
    if len(markers) != 5:
        raise ValueError(f"Expected 5 marker images, received {len(markers)}.")

    labels = [_classify_marker(marker) for marker in markers]
    return "".join(labels)
