"""Platform detection utilities for cross-platform support."""

from __future__ import annotations

import platform
import sys
from typing import Literal, Tuple


SystemType = Literal["windows", "linux"]
ArchType = Literal["x86_64", "aarch64", "arm64"]


def get_system() -> SystemType:
    """
    Detect the operating system.

    Returns:
        "windows" or "linux"

    Raises:
        RuntimeError: If the platform is not supported
    """
    system = platform.system().lower()

    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        raise RuntimeError(
            "macOS is not currently supported. "
            "Downloadyha supports Windows and Linux only."
        )
    else:
        raise RuntimeError(
            f"Unsupported operating system: {system}. "
            f"Downloadyha supports Windows and Linux only."
        )


def get_architecture() -> ArchType:
    """
    Detect the system architecture.

    Returns:
        "x86_64", "aarch64", or "arm64"

    Raises:
        RuntimeError: If the architecture is not supported
    """
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64", "x64"):
        return "x86_64"
    elif machine in ("aarch64", "arm64"):
        return "aarch64"
    elif machine.startswith("arm"):
        # ARM 32-bit is not supported
        raise RuntimeError(
            f"32-bit ARM architecture is not supported: {machine}. "
            f"Downloadyha requires 64-bit ARM (aarch64/arm64)."
        )
    else:
        raise RuntimeError(
            f"Unsupported architecture: {machine}. "
            f"Downloadyha supports x86_64 and aarch64 only."
        )


def get_platform_info() -> Tuple[SystemType, ArchType]:
    """
    Get both system and architecture information.

    Returns:
        Tuple of (system, architecture)
    """
    return get_system(), get_architecture()


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system().lower() == "windows"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system().lower() == "linux"


def get_exe_extension() -> str:
    """
    Get the executable extension for the current platform.

    Returns:
        ".exe" on Windows, "" on Linux
    """
    return ".exe" if is_windows() else ""
