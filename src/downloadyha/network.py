"""
network.py - Robust networking and SSL context management for Downloadyha.

Provides cross-platform HTTPS helpers, automated SSL root certificate bundle
resolution (via certifi and OS system stores), and fallback handlers for
environments with missing or broken local issuer certificates.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Union


# Standard Linux CA root certificate store locations across different distributions
LINUX_CA_BUNDLE_PATHS = [
    "/etc/ssl/certs/ca-certificates.crt",                  # Debian, Ubuntu, Arch, Gentoo
    "/etc/pki/tls/certs/ca-bundle.crt",                    # Fedora, RHEL 6, CentOS 6
    "/etc/ssl/ca-bundle.pem",                              # OpenSUSE
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",   # CentOS 7+, RHEL 7+, Rocky, Alma
    "/etc/ssl/cert.pem",                                   # Alpine, OpenBSD, FreeBSD, macOS
    "/etc/pki/tls/cert.pem",
    "/etc/certs/ca-certificates.crt",
    "/etc/ssl/certs/ca-bundle.crt",
]


def _find_ca_bundle() -> Optional[str]:
    """
    Locate a valid CA root certificate bundle file on the system.
    Checks certifi first, then environment variables, then known system paths.
    """
    # 1. Check certifi package bundle
    try:
        import certifi  # type: ignore
        certifi_path = certifi.where()
        if certifi_path and os.path.exists(certifi_path):
            return certifi_path
    except Exception:
        pass

    # 2. Check environment variables
    for env_var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        val = os.environ.get(env_var)
        if val and os.path.exists(val):
            return val

    # 3. Check known Linux CA bundle file paths
    for path in LINUX_CA_BUNDLE_PATHS:
        if os.path.exists(path):
            return path

    return None


def configure_ssl_environment() -> None:
    """
    Ensure SSL environment variables (SSL_CERT_FILE, REQUESTS_CA_BUNDLE)
    are populated so that Python standard library, requests, yt-dlp, and
    curl_cffi can locate trusted root certificates on any platform.
    """
    ca_bundle = _find_ca_bundle()
    if ca_bundle:
        os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)


# Auto-configure environment on module import
configure_ssl_environment()


def get_ssl_context(verify: bool = True) -> ssl.SSLContext:
    """
    Create an SSLContext configured for secure communication.

    Args:
        verify: Whether to perform certificate verification.

    Returns:
        Configured ssl.SSLContext.
    """
    if not verify:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    ca_bundle = _find_ca_bundle()
    if ca_bundle:
        try:
            return ssl.create_default_context(cafile=ca_bundle)
        except Exception:
            pass

    # Try default system context
    try:
        ctx = ssl.create_default_context()
        # On POSIX / Linux, load known CA bundle locations if possible
        if sys.platform != "win32":
            for path in LINUX_CA_BUNDLE_PATHS:
                if os.path.exists(path):
                    try:
                        ctx.load_verify_locations(cafile=path)
                        break
                    except Exception:
                        pass
        return ctx
    except Exception:
        pass

    # Fallback to unverified if verified context creation fails completely
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _is_ssl_verification_error(exc: Exception) -> bool:
    """Check if an exception is an SSL certificate verification failure."""
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True

    err_str = str(exc).lower()
    return any(
        phrase in err_str
        for phrase in (
            "certificate verify failed",
            "certificate_verify_failed",
            "unable to get local issuer certificate",
            "self signed certificate",
            "sslcertverificationerror",
            "certificaterror",
        )
    )


@contextlib.contextmanager
def open_url(
    url_or_request: Union[str, urllib.request.Request],
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None,
) -> Generator[Any, None, None]:
    """
    Context manager to open a URL or Request object with robust SSL support.
    Automatically handles SSL certificate verification and falls back to an
    unverified context if the local system CA store is missing or misconfigured.

    Args:
        url_or_request: URL string or urllib Request.
        timeout: Timeout in seconds.
        headers: Optional dictionary of HTTP headers.

    Yields:
        HTTPResponse object.
    """
    if isinstance(url_or_request, str):
        req = urllib.request.Request(url_or_request)
        req.add_header("User-Agent", "Downloadyha/2.0")
    else:
        req = url_or_request

    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    # Attempt 1: Standard verified SSL context
    ctx = get_ssl_context(verify=True)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            yield resp
            return
    except urllib.error.URLError as e:
        if _is_ssl_verification_error(e) or (hasattr(e, "reason") and _is_ssl_verification_error(e.reason)):
            # Attempt 2: Fallback to unverified SSL context for systems with missing local root CAs
            unverified_ctx = get_ssl_context(verify=False)
            with urllib.request.urlopen(req, context=unverified_ctx, timeout=timeout) as resp:
                yield resp
                return
        raise
    except ssl.SSLError as e:
        if _is_ssl_verification_error(e):
            unverified_ctx = get_ssl_context(verify=False)
            with urllib.request.urlopen(req, context=unverified_ctx, timeout=timeout) as resp:
                yield resp
                return
        raise


def download_url_to_file(
    url: str,
    dest_path: Path,
    timeout: int = 300,
    headers: Optional[Dict[str, str]] = None,
    show_progress: bool = True,
) -> None:
    """
    Download a file from a URL to destination path atomically with robust SSL.
    Optionally shows download progress for large files.

    Args:
        url: Remote URL to download.
        dest_path: Final destination path.
        timeout: Request timeout in seconds.
        headers: Optional HTTP headers.
        show_progress: Whether to show download progress.

    Raises:
        urllib.error.URLError / OSError: If the download fails.
    """
    from .ui import print_download, clear_progress_line, Colors

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest_path.with_suffix(dest_path.suffix + ".download.tmp")

    try:
        req_headers = {"User-Agent": "Downloadyha/2.0"}
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, headers=req_headers)

        with open_url(req, timeout=timeout) as response:
            # Get file size if available
            file_size = None
            try:
                file_size = int(response.headers.get("Content-Length", 0))
            except (ValueError, TypeError):
                pass

            # Show progress if requested and we have a size
            if show_progress and file_size > 0:
                downloaded = 0
                start_time = time.time()
                last_update = start_time

                # Initial progress message
                print_download(f"Downloading...", f"0% (0 MB / {file_size // (1024*1024)} MB)")

                with open(temp_dest, "wb") as f:
                    while True:
                        chunk = response.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Update progress every 0.5 seconds to avoid too frequent updates
                        now = time.time()
                        if now - last_update >= 0.5:
                            percent = (downloaded / file_size) * 100
                            speed = downloaded / (now - start_time) if now > start_time else 0
                            eta = (file_size - downloaded) / speed if speed > 0 else 0

                            from .ui import format_speed, format_bytes
                            speed_str = format_speed(speed)
                            eta_str = f"{int(eta//60):02d}:{int(eta)%60:02d}" if eta > 0 else "00:00"
                            downloaded_str = format_bytes(downloaded)
                            total_str = format_bytes(file_size)

                            clear_progress_line()
                            print_download(
                                f"Downloading...",
                                f"{percent:.1f}% ({downloaded_str} / {total_str}) {speed_str} ETA {eta_str}"
                            )
                            last_update = now

                # Final progress update
                clear_progress_line()
                from .ui import format_bytes
                print_download(
                    "Download complete",
                    f"100% ({format_bytes(file_size)} / {format_bytes(file_size)})"
                )
            else:
                # Original behavior for small files or when progress is disabled
                with open(temp_dest, "wb") as f:
                    shutil.copyfileobj(response, f)

        if temp_dest.exists():
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except OSError:
                    pass
            temp_dest.rename(dest_path)
    finally:
        if temp_dest.exists():
            try:
                temp_dest.unlink()
            except OSError:
                pass