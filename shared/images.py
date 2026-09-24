"""
TG Player - Image Processing Utilities
Provides smart square center-cropping, black bar (letterbox/pillarbox) trimming,
and dimension normalization for track covers, playlist covers, and user avatars.
"""
import io
import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


def crop_image_to_square(
    img_bytes: bytes,
    max_dimension: int = 1000,
    trim_black_bars: bool = True,
) -> Tuple[bytes, str]:
    """
    Crop an image (in bytes) to a 1:1 square with centering,
    optionally trimming video letterbox/pillarbox black borders (common in YouTube thumbnails),
    and resize if it exceeds max_dimension.

    Returns:
        (processed_bytes, extension) where extension is 'jpg' or 'png'
    """
    if not img_bytes or len(img_bytes) < 12:
        return img_bytes, "jpg"

    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            # Handle RGBA/transparency: keep PNG for transparency, convert others to RGB
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            if has_alpha:
                work_img = img.convert("RGBA")
                target_format = "PNG"
                ext = "png"
            else:
                work_img = img.convert("RGB")
                target_format = "JPEG"
                ext = "jpg"

            w, h = work_img.size

            # If already square (within 1% tolerance)
            if abs(w - h) <= max(2, int(min(w, h) * 0.01)):
                square_img = work_img
            else:
                # If image is non-square and trim_black_bars is enabled
                if trim_black_bars:
                    aspect = w / h if h > 0 else 1.0
                    # Check YouTube-style 4:3 letterboxing (e.g. 480x360 with black bars top/bottom)
                    if 1.25 <= aspect <= 1.45:
                        gray = work_img.convert("L")
                        bw = gray.point(lambda x: 255 if x > 18 else 0)
                        bbox = bw.getbbox()
                        if bbox:
                            _, top, _, bottom = bbox
                            if (top >= 10 or bottom <= h - 10) and (bottom - top) >= h * 0.6:
                                work_img = work_img.crop((0, top, w, bottom))

                # Center crop to 1:1 square
                cur_w, cur_h = work_img.size
                min_dim = min(cur_w, cur_h)
                left = (cur_w - min_dim) // 2
                top = (cur_h - min_dim) // 2
                square_img = work_img.crop((left, top, left + min_dim, top + min_dim))

            # Resize if dimensions exceed max_dimension
            sw, sh = square_img.size
            if sw > max_dimension or sh > max_dimension:
                square_img = square_img.resize((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            out = io.BytesIO()
            if target_format == "PNG":
                square_img.save(out, format="PNG", optimize=True)
            else:
                square_img.save(out, format="JPEG", quality=92, optimize=True)

            return out.getvalue(), ext
    except Exception as e:
        logger.warning(f"Error cropping image to square: {e}. Returning original bytes.")
        return img_bytes, "jpg"


def crop_image_file_to_square(
    file_path: str,
    max_dimension: int = 1000,
    trim_black_bars: bool = True,
) -> bool:
    """
    In-place crop of an image file on disk to a 1:1 square with centering.
    Returns True if successfully processed.
    """
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        processed_bytes, _ = crop_image_to_square(
            raw_bytes,
            max_dimension=max_dimension,
            trim_black_bars=trim_black_bars,
        )
        with open(file_path, "wb") as f:
            f.write(processed_bytes)
        return True
    except Exception as e:
        logger.warning(f"Error cropping image file {file_path}: {e}")
        return False
