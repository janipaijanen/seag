# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Pinned differential and property checks for shared validation primitives."""

import ipaddress
import json
from pathlib import Path
import unittest

from defusedxml import ElementTree as DefusedElementTree
from defusedxml.common import DefusedXmlException
from hypothesis import given, settings, strategies as st
from jsonschema import Draft202012Validator
from langcodes import tag_is_valid
import rfc3986
from rfc3986.exceptions import ValidationError as Rfc3986ValidationError
from rfc3986.validators import Validator as Rfc3986Validator

from seag.cxl import export
from seag.validation import (
    absolute_iri,
    ipv4_address,
    ipv6_address,
    iso_timestamp,
    language_tag,
    port_number,
    strict_json_loads,
)


ROOT = Path(__file__).resolve().parents[1]
DETERMINISTIC = settings(max_examples=200, derandomize=True, database=None)


class ValidationOracleTest(unittest.TestCase):
    @DETERMINISTIC
    @given(st.integers(min_value=-131072, max_value=131072))
    def test_port_range_property(self, value):
        self.assertEqual(0 <= value <= 65535, port_number(value))

    @DETERMINISTIC
    @given(st.ip_addresses(v=4))
    def test_ipv4_accepts_canonical_stdlib_addresses(self, value):
        rendered = str(value)
        self.assertEqual(rendered, str(ipaddress.IPv4Address(rendered)))
        self.assertTrue(ipv4_address(rendered))

    @DETERMINISTIC
    @given(st.ip_addresses(v=6))
    def test_ipv6_accepts_stdlib_addresses_without_zones(self, value):
        self.assertTrue(ipv6_address(str(value)))

    @DETERMINISTIC
    @given(st.one_of(st.none(), st.booleans(), st.integers(), st.text()))
    def test_strict_json_round_trip_for_scalar_values(self, value):
        encoded = json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8")
        self.assertEqual(value, strict_json_loads(encoded))

    def test_language_profile_is_explicitly_narrower_than_registry_validation(self):
        for tag in ("en", "en-GB", "fi", "zh-Hant-TW", "de-CH-1901", "i-klingon"):
            with self.subTest(tag=tag):
                self.assertTrue(language_tag(tag))
                self.assertTrue(tag_is_valid(tag))
        self.assertTrue(language_tag("zz"), "the core intentionally checks syntax only")
        self.assertFalse(tag_is_valid("zz"), "the pinned oracle also checks registry membership")

    def test_uri_oracle_and_seag_policy_boundaries_are_explicit(self):
        validator = Rfc3986Validator().require_presence_of("scheme").check_validity_of(
            "scheme", "host", "port"
        )
        for value in (
            "https://example.invalid/path",
            "urn:uuid:12345678-1234-4234-8234-123456789abc",
            "urn:neutral:?\ue000",
        ):
            with self.subTest(value=value):
                validator.validate(rfc3986.uri_reference(value))
                self.assertTrue(absolute_iri(value))
        over_range_port = "https://example.invalid:65536/path"
        with self.assertRaises(Rfc3986ValidationError):
            validator.validate(rfc3986.uri_reference(over_range_port))
        self.assertFalse(absolute_iri(over_range_port))
        internationalized = "https://example.invalid/ä"
        validator.validate(rfc3986.uri_reference(internationalized))
        self.assertTrue(absolute_iri(internationalized), "SEAG's declared field accepts an RFC 3987 IRI")
        for policy_rejection in (
            "https://",
            "https://example.invalid/%GG",
            "urn:thing[bad",
            "https://user@@example.org/x",
            "https://example.org/a[b]",
            "https://example.org/#a#b",
            "urn:neutral:\ufdd0",
            "urn:neutral:#\ue000",
        ):
            with self.subTest(policy_rejection=policy_rejection):
                self.assertFalse(absolute_iri(policy_rejection))

    def test_rfc3339_offset_components_are_bounded(self):
        for value in (
            "2026-11-22T12:34:56Z",
            "2026-11-22T12:34:56+00:00",
            "2026-11-22T12:34:56-23:59",
        ):
            with self.subTest(value=value):
                self.assertTrue(iso_timestamp(value))
        for value in (
            "2026-11-22T12:34:56+01:60",
            "2026-11-22T12:34:56+00:99",
            "2026-11-22T12:34:56+24:00",
        ):
            with self.subTest(value=value):
                self.assertFalse(iso_timestamp(value))

    def test_source_schema_and_retained_fixtures_validate_with_pinned_jsonschema(self):
        schema = strict_json_loads((ROOT / "schema/source-0.1.schema.json").read_bytes())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        for name in ("manifest.json", "fragment.json", "variant.json"):
            with self.subTest(name=name):
                instance = strict_json_loads((ROOT / "fixtures/valid" / name).read_bytes())
                self.assertEqual([], list(validator.iter_errors(instance)))

    def test_cxl_is_accepted_by_defused_parser_and_hostile_dtd_is_rejected(self):
        cxl, _provenance, _expected = export(
            ROOT / "fixtures/valid/manifest.json",
            "2026-11-22T00:00:00Z",
        )
        DefusedElementTree.fromstring(
            cxl,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
        hostile = b"<!DOCTYPE cmap [<!ENTITY x 'expanded'>]><cmap>&x;</cmap>"
        with self.assertRaises(DefusedXmlException):
            DefusedElementTree.fromstring(
                hostile,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True,
            )


if __name__ == "__main__":
    unittest.main()
