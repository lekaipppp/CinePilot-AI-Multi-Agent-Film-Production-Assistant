"""
Pagination helpers used by list endpoints.
"""

from typing import Any, Dict


def paginate_params(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Return validated pagination params (cap limit at 200)."""
    return {"limit": min(limit, 200), "offset": max(offset, 0)}
