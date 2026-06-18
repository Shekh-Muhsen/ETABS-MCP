"""
HTTP security middleware for the ETABS MCP server.

Provides ``SecFetchMiddleware``, a Starlette middleware that rejects
browser-initiated cross-origin requests based on the ``Sec-Fetch-Site``
header.  This is a defense-in-depth layer on top of the MCP SDK's
built-in ``TransportSecurityMiddleware`` (Host / Origin validation).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

_BLOCKED_SEC_FETCH_SITE_VALUES = frozenset({"cross-site", "same-site"})


class SecFetchMiddleware(BaseHTTPMiddleware):
    """Reject HTTP requests with dangerous ``Sec-Fetch-Site`` values."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        sec_fetch_site = request.headers.get("sec-fetch-site", "")
        if sec_fetch_site in _BLOCKED_SEC_FETCH_SITE_VALUES:
            return Response(
                content="Forbidden: cross-origin requests are not allowed.",
                status_code=403,
                media_type="text/plain",
            )
        return await call_next(request)
