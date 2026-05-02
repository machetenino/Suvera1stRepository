"""Drawing image loading and preparation for the take-off agent."""

import base64
import io
import logging
from pathlib import Path

from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

# Architectural drawings have fine lines and small text — keep resolution high
MAX_LONG_EDGE = 4096
MIN_LONG_EDGE = 1024


def load_drawing(path: Path) -> list[Image.Image]:
    """Load a drawing from a PDF or image file. Returns a list of PIL Images (one per page)."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
        return [_load_image(path)]
    raise ValueError(
        f"Unsupported file type '{suffix}'. "
        "Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP"
    )


def _load_pdf(path: Path) -> list[Image.Image]:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError(
            "pdf2image is required for PDF support.\n"
            "  pip install pdf2image\n"
            "  Mac:   brew install poppler\n"
            "  Linux: apt-get install poppler-utils"
        )

    logger.info(f"Converting PDF to images at 300 DPI: {path}")
    images = convert_from_path(str(path), dpi=300, fmt="png")
    logger.info(f"Converted {len(images)} page(s) from PDF")
    return images


def _load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    return img


def prepare_for_api(
    image: Image.Image,
    enhance_contrast: bool = True,
    target_long_edge: int = MAX_LONG_EDGE,
) -> dict:
    """
    Resize, optionally enhance, and base64-encode an image for the Anthropic API.
    Returns a source dict suitable for use in a message content block.
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    image = _resize(image, target_long_edge)

    if enhance_contrast:
        # Mild contrast + sharpness boost to make lines and text more legible
        image = ImageEnhance.Contrast(image).enhance(1.2)
        image = ImageEnhance.Sharpness(image).enhance(1.3)

    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    encoded = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    logger.info(
        f"Prepared image for API: {image.size[0]}x{image.size[1]} px, "
        f"{len(buf.getvalue()) / 1024:.1f} KB"
    )

    return {
        "type": "base64",
        "media_type": "image/png",
        "data": encoded,
    }


def _resize(image: Image.Image, max_long_edge: int) -> Image.Image:
    w, h = image.size
    long_edge = max(w, h)

    if MIN_LONG_EDGE <= long_edge <= max_long_edge:
        return image

    target = max_long_edge if long_edge > max_long_edge else MIN_LONG_EDGE
    scale = target / long_edge
    return image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
