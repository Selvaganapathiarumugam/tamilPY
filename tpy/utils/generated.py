"""
Markers and safe writes for framework-generated source files.

Format (first line)::

    # tpy:generated:sha256:<hex digest of body>

The digest covers everything after the marker line. Matching digest means
the file is pristine; mismatch or missing marker means manual edits.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from tpy.exceptions import GeneratedFileConflict
from tpy.utils.file_manager import FileManager

MARKER_PREFIX = "# tpy:generated:sha256:"
_MARKER_RE = re.compile(
    rf"^{re.escape(MARKER_PREFIX)}([0-9a-fA-F]{{64}})\r?\n",
    re.MULTILINE,
)


def content_digest(body: str) -> str:
    """Return SHA-256 hex digest of ``body`` (UTF-8)."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def with_marker(body: str) -> str:
    """Prepend a generated marker line for ``body``."""
    return f"{MARKER_PREFIX}{content_digest(body)}\n{body}"


def split_marker(text: str) -> tuple[str | None, str]:
    """
    Split marker hash and body from file text.

    Returns:
        ``(hash_or_None, body)``. Body excludes the marker line when present.
    """
    match = _MARKER_RE.match(text)
    if not match:
        return None, text
    return match.group(1).lower(), text[match.end() :]


def is_pristine(path: Path | str) -> bool:
    """
    Return True when the file is missing or its marker matches the body.

    Legacy files without a marker are treated as edited (not pristine).
    """
    file_path = Path(path)
    if not file_path.exists():
        return True
    marker_hash, body = split_marker(FileManager.read(file_path))
    if marker_hash is None:
        return False
    return marker_hash == content_digest(body)


def write_generated(
    path: Path | str,
    body: str,
    *,
    force: bool = False,
) -> None:
    """
    Write ``body`` with a generated marker, protecting manual edits.

    Args:
        path: Destination file.
        body: Generated content without marker.
        force: When True, overwrite even if the file was edited.

    Raises:
        GeneratedFileConflict: Existing file looks manually edited and
            ``force`` is False.
    """
    file_path = Path(path)
    if file_path.exists() and not force and not is_pristine(file_path):
        raise GeneratedFileConflict(str(file_path))
    FileManager.write(file_path, with_marker(body))
