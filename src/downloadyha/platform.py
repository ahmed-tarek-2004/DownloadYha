"""
Platform and architecture detection utilities for Downloadyha.
"""

from __future__ import annotations

import platform as _sys_platform
from typing import Tuple


def get_platform() -> str:
    """
    Get the current platform identifier.

    Returns:
        "windows" or "linux"
    """
    system = _sys_platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return "linux"


def get_architecture() -> str:
    """
    Get the current architecture identifier.

    Returns:
        "x86_64" or "aarch64"
    """
    machine = _sys_platform.machine().lower()
    if machine in ("amd64", "x86_64", "x64"):
        return "x86_64"
    elif machine in ("arm64", "aarch64"):
        return "aarch64"
    else:
        return "x86_64"


def get_platform_info() -> Tuple[str, str]:
    """
    Get both platform and architecture.

    Returns:
        Tuple of (platform, architecture)
    """
    return get_platform(), get_architecture()


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "windows"


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == "linux"
