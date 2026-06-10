"""
CLI entry point for the ETABS MCP server.
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import sys
import warnings

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from etabs_mcp.file_io.validation import validate_args_allowed_dirs
from etabs_mcp.http_middleware import SecFetchMiddleware
from etabs_mcp.server import create_mcp_server

warnings.filterwarnings("ignore", message="authlib.jose module is deprecated")

_HTTP_ONLY_DEFAULTS = {"port": 18121, "token": None}
_MCP_TRANSPORT_DEFAULT = "stdio"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="etabs-mcp",
        description="MCP server for CSI ETABS via the ETABS COM API",
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=_MCP_TRANSPORT_DEFAULT,
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    parser.add_argument(
        "--allowed-dirs",
        type=str,
        nargs="+",
        default=None,
        help="Directories the ETABS MCP server can access for file I/O (space separated)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_HTTP_ONLY_DEFAULTS["port"],
        help=f"[http] TCP port to listen on (default: {_HTTP_ONLY_DEFAULTS['port']})",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("ETABS_MCP_TOKEN"),
        help="[http] Bearer token (or set ETABS_MCP_TOKEN env var)",
    )

    args = parser.parse_args(argv)

    if args.transport == "stdio":
        for opt, default in _HTTP_ONLY_DEFAULTS.items():
            if getattr(args, opt) != default:
                flag = f"--{opt.replace('_', '-')}"
                warnings.warn(
                    f"{flag} has no effect in stdio mode (requires --transport http)",
                    stacklevel=2,
                )
    return args


def setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )
    logging.info(f"Logging initialized at {log_level} level")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    setup_logging(args.log_level)
    allowed_dirs = validate_args_allowed_dirs(args.allowed_dirs)

    if args.transport == "stdio":
        mcp = create_mcp_server(allowed_dirs)
        try:
            mcp.run(transport="stdio", show_banner=False)
        except KeyboardInterrupt:
            logging.info("Shutting down ETABS MCP server")

    else:  # http
        token = args.token
        if not token:
            token = secrets.token_urlsafe(32)
            logging.warning(
                "No --token provided; auto-generated token for this session: %s",
                token,
            )
        fastmcp_kwargs = {
            "auth": StaticTokenVerifier(
                tokens={token: {"client_id": "authorized-user", "scopes": ["read:data"]}},
                required_scopes=["read:data"],
            )
        }
        mcp = create_mcp_server(allowed_dirs, fastmcp_kwargs=fastmcp_kwargs)
        try:
            mcp.run(
                transport="http",
                host="127.0.0.1",
                port=args.port,
                stateless_http=True,
                middleware=[
                    Middleware(SecFetchMiddleware),
                    Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"]),
                ],
            )
        except KeyboardInterrupt:
            logging.info("Shutting down ETABS MCP server")


if __name__ == "__main__":
    main()
