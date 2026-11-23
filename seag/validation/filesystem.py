# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Confined regular-file reads shared by validation and transformation paths."""

from __future__ import annotations

import os
from pathlib import Path
import stat


def read_confined_regular(root: Path, relative: str) -> bytes:
    """Read one regular file without following any path-component symlink."""
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe fragment path: {relative!r}")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise OSError("secure nonblocking fragment reads are unavailable")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    directory = os.open(root, directory_flags)
    try:
        for component in path.parts[:-1]:
            child = os.open(
                component,
                directory_flags | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        descriptor = os.open(
            path.parts[-1],
            os.O_RDONLY
            | os.O_NOFOLLOW
            | os.O_NONBLOCK
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory,
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(f"fragment is not a regular file: {relative!r}")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                return handle.read()
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)
