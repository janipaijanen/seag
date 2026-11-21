# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for truthful, multi-holder SPDX copyright declarations."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_spdx", ROOT / "scripts" / "check-spdx.py"
)
CHECK_SPDX = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECK_SPDX)


class CopyrightDeclarationTest(unittest.TestCase):
    def test_accepts_maintainer_or_contributor_ownership(self):
        for owner in (
            "Copyright (C) 2026 Jani Päijänen",
            "Copyright (C) 2027 Example Contributor",
        ):
            with self.subTest(owner=owner):
                text = f"# SPDX-FileCopyrightText: {owner}"
                self.assertEqual([owner], CHECK_SPDX.copyright_declarations(text))

    def test_preserves_multiple_rights_holders(self):
        text = """<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-FileCopyrightText: Copyright (C) 2027 Example Contributor -->"""
        self.assertEqual(
            [
                "Copyright (C) 2026 Jani Päijänen",
                "Copyright (C) 2027 Example Contributor",
            ],
            CHECK_SPDX.copyright_declarations(text),
        )

    def test_rejects_missing_or_empty_value(self):
        for text in ("", "# SPDX-FileCopyrightText:", "<!-- SPDX-FileCopyrightText: -->"):
            with self.subTest(text=text):
                self.assertEqual([], CHECK_SPDX.copyright_declarations(text))


if __name__ == "__main__":
    unittest.main()
