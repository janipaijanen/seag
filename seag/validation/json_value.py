# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Strict RFC 8259 JSON decoding shared by SEAG inputs and evidence."""

from __future__ import annotations

import json
import math


def strict_json_loads(raw: str | bytes) -> object:
    """Decode one UTF-8 JSON value without duplicate names or non-finite numbers."""

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    def object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for name, value in pairs:
            if name in result:
                raise ValueError(f"duplicate JSON object member: {name!r}")
            result[name] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON number forbidden: {value}")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"non-finite JSON number forbidden: {value}")
        return parsed

    return json.loads(
        raw,
        object_pairs_hook=object_from_pairs,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )
