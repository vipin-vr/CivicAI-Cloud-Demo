from __future__ import annotations

import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import image_uploads


def encoded_image(image: Image.Image, image_format: str, **save_options: object) -> bytes:
    output = BytesIO()
    image.save(output, format=image_format, **save_options)
    return output.getvalue()


class ImageUploadSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.private_root = Path(self.temp_dir.name) / "private-uploads"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_jpeg_png_and_webp_are_sanitized_to_jpeg(self) -> None:
        for image_format in ("JPEG", "PNG", "WEBP"):
            with self.subTest(image_format=image_format):
                source = Image.new("RGB", (12, 8), "blue")
                sanitized = image_uploads.sanitize_image(encoded_image(source, image_format))
                self.assertEqual(sanitized.mime_type, "image/jpeg")
                with Image.open(BytesIO(sanitized.data)) as result:
                    self.assertEqual(result.format, "JPEG")
                    self.assertEqual(result.mode, "RGB")

    def test_invalid_and_oversized_raw_files_are_rejected(self) -> None:
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.sanitize_image(b"not an image")
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.sanitize_image(b"x" * (image_uploads.MAX_UPLOAD_BYTES + 1))
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.sanitize_image(encoded_image(Image.new("RGB", (5, 5)), "BMP"))

    def test_dimension_and_pixel_limits_are_rejected_before_decode(self) -> None:
        too_wide = encoded_image(Image.new("1", (6_001, 1)), "PNG")
        too_many_pixels = encoded_image(Image.new("1", (5_000, 4_001)), "PNG")
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.sanitize_image(too_wide)
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.sanitize_image(too_many_pixels)

    def test_decompression_bomb_warning_is_rejected(self) -> None:
        raw = encoded_image(Image.new("RGB", (2, 2)), "PNG")
        original_limit = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = 1
            with self.assertRaises(image_uploads.ImageUploadError):
                image_uploads.sanitize_image(raw)
        finally:
            Image.MAX_IMAGE_PIXELS = original_limit

    def test_orientation_transparency_and_metadata_are_removed(self) -> None:
        source = Image.new("RGBA", (3, 2), (255, 0, 0, 0))
        source.putpixel((1, 1), (0, 0, 255, 255))
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "private metadata"
        sanitized = image_uploads.sanitize_image(encoded_image(source, "PNG", exif=exif))
        with Image.open(BytesIO(sanitized.data)) as result:
            self.assertEqual(result.size, (2, 3))
            self.assertEqual(result.getexif().get(270), None)
            white_pixel = result.convert("RGB").getpixel((0, 0))
            self.assertGreaterEqual(min(white_pixel), 220)

    def test_private_storage_uses_safe_uuid_names_atomic_writes_and_approved_roots(self) -> None:
        sanitized = image_uploads.sanitize_image(encoded_image(Image.new("RGB", (8, 8), "green"), "PNG"))
        stored = image_uploads.store_sanitized_image(sanitized, self.private_root)
        self.assertTrue(stored.exists())
        self.assertEqual(stored.suffix, ".jpg")
        self.assertEqual(len(stored.stem), 32)
        self.assertEqual(stored.read_bytes(), sanitized.data)
        self.assertTrue(image_uploads.is_approved_image_path(str(stored), self.private_root))
        self.assertFalse(image_uploads.is_approved_image_path(str(Path(self.temp_dir.name) / "outside.jpg"), self.private_root))
        with self.assertRaises(image_uploads.ImageUploadError):
            image_uploads.validate_private_upload_root(image_uploads.PROJECT_ROOT / "private-uploads")
        self.assertFalse(list(self.private_root.glob(".upload-*.tmp")))

    def test_failed_atomic_write_leaves_no_partial_file(self) -> None:
        sanitized = image_uploads.sanitize_image(encoded_image(Image.new("RGB", (8, 8)), "JPEG"))
        with patch("image_uploads.os.replace", side_effect=OSError("simulated write failure")):
            with self.assertRaises(image_uploads.ImageUploadError):
                image_uploads.store_sanitized_image(sanitized, self.private_root)
        self.assertFalse(list(self.private_root.glob(".upload-*.tmp")))
        self.assertFalse(list(self.private_root.glob("*.jpg")))

    def test_legacy_rendering_is_limited_to_approved_legacy_root(self) -> None:
        legacy_root = Path(self.temp_dir.name) / "legacy-uploads"
        legacy_root.mkdir()
        legacy_file = legacy_root / "legacy-image.jpg"
        with patch.object(image_uploads, "LEGACY_UPLOAD_ROOT", legacy_root):
            legacy_file.write_bytes(encoded_image(Image.new("RGB", (2, 2)), "JPEG"))
            self.assertTrue(image_uploads.is_approved_image_path(str(legacy_file), self.private_root))


if __name__ == "__main__":
    unittest.main()
