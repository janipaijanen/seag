# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Bounded lexical validators; validation never rewrites authored values."""

from __future__ import annotations

import datetime
import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit


GRANDFATHERED_LANGUAGE_TAGS = {
    "art-lojban", "cel-gaulish", "en-gb-oed", "i-ami", "i-bnn",
    "i-default", "i-enochian", "i-hak", "i-klingon", "i-lux",
    "i-mingo", "i-navajo", "i-pwn", "i-tao", "i-tay", "i-tsu",
    "no-bok", "no-nyn", "sgn-be-fr", "sgn-be-nl", "sgn-ch-de",
    "zh-guoyu", "zh-hakka", "zh-min", "zh-min-nan", "zh-xiang",
}
ALNUM_SUBTAG = re.compile(r"^[A-Za-z0-9]+$")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
INVALID_IRI_ASCII = frozenset('<>"{}|\\^`')


def iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def iso_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        return False
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def port_number(value: object) -> bool:
    """Return whether value is an uncoerced 16-bit Internet port number."""

    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535


def ipv4_address(value: object) -> bool:
    """Return whether value is an unambiguous dotted-decimal IPv4 address."""

    if not isinstance(value, str):
        return False
    try:
        return str(ipaddress.IPv4Address(value)) == value
    except ipaddress.AddressValueError:
        return False


def ipv6_address(value: object) -> bool:
    """Return whether value is an IPv6 address without an interface zone ID."""

    if not isinstance(value, str) or "%" in value:
        return False
    try:
        ipaddress.IPv6Address(value)
        return True
    except ipaddress.AddressValueError:
        return False


def language_tag(value: object) -> bool:
    if not isinstance(value, str) or value.casefold() in GRANDFATHERED_LANGUAGE_TAGS:
        return isinstance(value, str) and value.casefold() in GRANDFATHERED_LANGUAGE_TAGS
    subtags = value.split("-")
    if not subtags or any(not part or len(part) > 8 or not ALNUM_SUBTAG.fullmatch(part) for part in subtags):
        return False
    index = 0
    language = subtags[index]
    if not language.isalpha() or not 2 <= len(language) <= 8:
        if language.casefold() != "x":
            return False
    if language.casefold() == "x":
        return len(subtags) > 1
    index += 1
    if len(language) in (2, 3):
        extlang_count = 0
        while index < len(subtags) and len(subtags[index]) == 3 and subtags[index].isalpha() and extlang_count < 3:
            index += 1
            extlang_count += 1
    if index < len(subtags) and len(subtags[index]) == 4 and subtags[index].isalpha():
        index += 1
    if index < len(subtags) and (
        (len(subtags[index]) == 2 and subtags[index].isalpha())
        or (len(subtags[index]) == 3 and subtags[index].isdigit())
    ):
        index += 1
    variants: set[str] = set()
    while index < len(subtags) and (
        5 <= len(subtags[index]) <= 8
        or (len(subtags[index]) == 4 and subtags[index][0].isdigit())
    ):
        variant = subtags[index].casefold()
        if variant in variants:
            return False
        variants.add(variant)
        index += 1
    singletons: set[str] = set()
    while index < len(subtags) and len(subtags[index]) == 1 and subtags[index].casefold() != "x":
        singleton = subtags[index].casefold()
        if singleton in singletons:
            return False
        singletons.add(singleton)
        index += 1
        start = index
        while index < len(subtags) and 2 <= len(subtags[index]) <= 8:
            index += 1
        if index == start:
            return False
    if index < len(subtags) and subtags[index].casefold() == "x":
        index += 1
        start = index
        while index < len(subtags) and 1 <= len(subtags[index]) <= 8:
            index += 1
        if index == start:
            return False
    return index == len(subtags)


def absolute_iri(value: object) -> bool:
    if not isinstance(value, str) or not value or any(
        character.isspace()
        or unicodedata.category(character) in {"Cc", "Cs"}
        or character in INVALID_IRI_ASCII
        for character in value
    ):
        return False
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        return False
    scheme, separator, remainder = value.partition(":")
    if not separator or not SCHEME.fullmatch(scheme) or not remainder:
        return False
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
        port = parts.port
    except ValueError:
        return False
    if parts.scheme.casefold() in {"http", "https"}:
        if not (remainder.startswith("//") and parts.netloc and hostname):
            return False
        if port is not None and not port_number(port):
            return False
        if ":" in hostname and not ipv6_address(hostname):
            return False
        if "." in hostname and re.fullmatch(r"[0-9.]+", hostname) and not ipv4_address(hostname):
            return False
        return True
    return parts.scheme.casefold() == scheme.casefold()
