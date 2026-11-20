"""Validation and private storage for citizen-uploaded images."""
from __future__ import annotations

import os
import tempfile
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_WIDTH = 6_000
MAX_IMAGE_HEIGHT = 6_000
MAX_IMAGE_PIXELS = 20_000_000
JPEG_MIME_TYPE = "image/jpeg"
PROJECT_ROOT = Path(__file__).resolve().parent
LEGACY_UPLOAD_ROOT = PROJECT_ROOT / "uploads"


class ImageUploadError(ValueError):
    """Raised for invalid, unsafe, or unstoreable image uploads."""


@dataclass(frozen=True)
class SanitizedImage:
    data: bytes
    mime_type: str = JPEG_MIME_TYPE


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def configured_private_upload_root() -> Path:
    """Return the configured private root, with an OS data-directory default."""
    configured = os.getenv("CIVICAI_UPLOAD_DIR")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        return Path(os.getenv("PROGRAMDATA", r"C:\ProgramData")) / "CivicAI" / "uploads"
    return Path("/var/lib/civicai/uploads")


def validate_private_upload_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    onedrive_root = os.getenv("OneDrive")
    is_onedrive_path = any(part.casefold() == "onedrive" for part in resolved.parts)
    if _inside(resolved, PROJECT_ROOT) or is_onedrive_path or (onedrive_root and _inside(resolved, Path(onedrive_root))):
        raise ImageUploadError("Private upload storage must be outside the project and OneDrive directories.")
    return resolved


def sanitize_image(raw_bytes: bytes) -> SanitizedImage:
    """Fully decode a safe image and return a metadata-free JPEG representation."""
    if not raw_bytes or len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise ImageUploadError("Image must be 10 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw_bytes)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ImageUploadError("Only JPEG, PNG, and WebP images are accepted.")
                width, height = source.size
                if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT or width * height > MAX_IMAGE_PIXELS:
                    raise ImageUploadError("Image dimensions exceed the supported limit.")
                source.load()
                oriented = ImageOps.exif_transpose(source)
                if oriented.mode in {"RGBA", "LA"} or (oriented.mode == "P" and "transparency" in oriented.info):
                    background = Image.new("RGBA", oriented.size, "white")
                    background.alpha_composite(oriented.convert("RGBA"))
                    rgb_image = background.convert("RGB")
                else:
                    rgb_image = oriented.convert("RGB")
                output = BytesIO()
                rgb_image.save(output, format="JPEG", quality=90, optimize=True)
    except ImageUploadError:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError, Image.UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageUploadError("The uploaded file is not a safe, valid image.") from error
    jpeg_bytes = output.getvalue()
    if len(jpeg_bytes) > MAX_UPLOAD_BYTES:
        raise ImageUploadError("Processed image exceeds the 10 MB limit.")
    return SanitizedImage(jpeg_bytes)


def store_sanitized_image(image: SanitizedImage, root: Path | None = None) -> Path:
    """Atomically store a sanitized JPEG under a private, application-owned root."""
    upload_root = validate_private_upload_root(root or configured_private_upload_root())
    upload_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(upload_root, 0o700)
    except OSError:
        pass
    destination = upload_root / f"{uuid4().hex}.jpg"
    if not _inside(destination, upload_root):
        raise ImageUploadError("Invalid private upload destination.")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=upload_root, prefix=".upload-", suffix=".tmp", delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(image.data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        try:
            os.chmod(temporary_path, 0o600)
        except OSError:
            pass
        os.replace(temporary_path, destination)
        temporary_path = None
        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
        return destination
    except OSError as error:
        raise ImageUploadError("The image could not be stored securely.") from error
    finally:
        if temporary_path:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def is_approved_image_path(path_value: str | None, private_root: Path | None = None) -> bool:
    """Allow current private uploads and legacy uploads, never arbitrary database paths."""
    if not path_value:
        return False
    candidate = Path(path_value)
    if not candidate.exists() or not candidate.is_file():
        return False
    roots = [LEGACY_UPLOAD_ROOT]
    try:
        roots.append(validate_private_upload_root(private_root or configured_private_upload_root()))
    except ImageUploadError:
        pass
    return any(_inside(candidate, root) for root in roots)
