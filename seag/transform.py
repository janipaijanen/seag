# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Shared deterministic transformation helpers."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import re

from .validation import iso_timestamp


def timestamp(value: str | None) -> str:
    if value:
        if not iso_timestamp(value):
            raise ValueError("generated timestamp must be RFC 3339 with a UTC offset")
        return value
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is None:
        raise ValueError("generated timestamp requires --generated-at or SOURCE_DATE_EPOCH")
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)", epoch):
        raise ValueError("SOURCE_DATE_EPOCH must be a canonical nonnegative decimal integer")
    try:
        moment = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        raise ValueError("SOURCE_DATE_EPOCH is outside the supported timestamp range") from error
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_with_provenance(output: Path, value: object, provenance: dict, sidecar: Path | None = None) -> tuple[Path, Path]:
    data = json_bytes(value)
    output.write_bytes(data)
    provenance["output_sha256"] = hashlib.sha256(data).hexdigest()
    target = sidecar or output.with_name(output.name + ".provenance.json")
    target.write_bytes(json_bytes(provenance))
    return output, target
