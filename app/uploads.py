# Metadata stripping for uploads (US-016).
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from PIL import Image

from app.config import get_settings

settings = get_settings()


def strip_image_metadata(file_path: Path) -> None:
    """Strip EXIF and other metadata from image; overwrite file."""
    try:
        img = Image.open(file_path)
        data = list(img.getdata())
        no_exif = Image.new(img.mode, img.size)
        no_exif.putdata(data)
        no_exif.save(file_path, format=img.format or "PNG")
    except Exception:
        raise ValueError("Could not strip image metadata or save file")


def allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in settings.allowed_image_extensions
