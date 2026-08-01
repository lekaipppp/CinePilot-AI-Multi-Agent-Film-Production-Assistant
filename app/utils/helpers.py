"""
Miscellaneous helpers.
"""

import re
import uuid


def is_valid_uuid(value: str) -> bool:
    """Return True if the string is a valid UUID v4."""
    try:
        uuid.UUID(str(value), version=4)
        return True
    except ValueError:
        return False


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)
