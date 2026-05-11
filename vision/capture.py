"""Screen capture using mss. Fast on Windows (GDI-backed)."""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Optional

import mss
from PIL import Image


@dataclass
class Frame:
    jpeg: bytes
    width: int
    height: int
    mime: str = "image/jpeg"
    _pil_cache: Optional[Image.Image] = field(
        default=None, repr=False, compare=False, init=False,
    )

    def to_pil(self) -> Image.Image:
        if self._pil_cache is None:
            self._pil_cache = Image.open(io.BytesIO(self.jpeg))
        return self._pil_cache


class ScreenCapture:
    def __init__(self, *, monitor_index: int = 1, max_edge_px: int = 768, jpeg_quality: int = 80) -> None:
        self._monitor_index = monitor_index
        self._max_edge = max_edge_px
        self._quality = jpeg_quality
        # mss instances are not threadsafe; one per thread.
        self._sct: Optional[mss.mss] = None

    def _ensure(self) -> mss.mss:
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct

    def grab(self) -> Frame:
        sct = self._ensure()
        mon = sct.monitors[self._monitor_index]
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.rgb)

        # Downscale to max_edge_px.
        w, h = img.size
        scale = min(1.0, self._max_edge / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self._quality)
        return Frame(jpeg=buf.getvalue(), width=img.size[0], height=img.size[1])

    def close(self) -> None:
        if self._sct is not None:
            self._sct.close()
            self._sct = None


def downscale_jpeg(jpeg_bytes: bytes, max_edge: int = 512, quality: int = 50) -> bytes:
    """Re-encode JPEG at lower resolution/quality for LLM consumption."""
    img = Image.open(io.BytesIO(jpeg_bytes))
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
