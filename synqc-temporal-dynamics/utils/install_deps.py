"""
Dependency bootstrap helpers for SynQc Temporal Dynamics.

This module installs the core data dependencies (Pandas 3.x and NumPy)
required by the runtime and notebook helpers. It can be invoked from
CLI, notebooks, or CI to ensure the environment is ready.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def _pip_install(packages: Iterable[str], extra_args: List[str]) -> None:
    """Install the provided packages via pip, emitting progress messages."""
    for pkg in packages:
        print(f"Installing {pkg} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *extra_args, pkg])


def install_pandas3_numpy(*, wheel_dir: Path | None = None) -> None:
    """
    Install Pandas 3.x and NumPy in the current Python environment.

    This function:
    - Pins pandas to major version 3 (per project requirement)
    - Installs/updates numpy afterwards
    - Works in notebooks, CLI scripts, and automated test runners
    - Supports offline installs when you supply a wheel directory
    """
    pkgs = [
        "pandas>=3.0,<4.0",  # Project requirement
        "numpy",             # Latest compatible version
    ]

    pip_args: List[str] = []
    if wheel_dir is not None:
        pip_args = ["--no-index", "--find-links", str(wheel_dir)]

    _pip_install(pkgs, pip_args)
    print("\nInstallation complete. Pandas 3.x + NumPy ready to use.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install pandas 3.x and numpy")
    parser.add_argument(
        "--wheel-dir",
        type=Path,
        help="Optional path to a directory of pre-downloaded wheels (for offline installs).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    install_pandas3_numpy(wheel_dir=args.wheel_dir)
