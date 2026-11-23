# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "check-dependency-policy.py"
SPEC = importlib.util.spec_from_file_location("dependency_policy", SCRIPT)
dependency_policy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(dependency_policy)


class DependencyPolicyVersionTest(unittest.TestCase):
    def test_supported_release_versions_have_pep440_metadata(self):
        cases = {
            "0.2.0-alpha.2": "0.2.0a2",
            "1.0.0-beta.3": "1.0.0b3",
            "1.0.0-rc.1": "1.0.0rc1",
            "1.0.0": "1.0.0",
        }
        for version, expected in cases.items():
            with self.subTest(version=version):
                self.assertEqual(expected, dependency_policy.pep440_version(version))

    def test_unsupported_release_metadata_fails_closed(self):
        for version in ("v1.0.0", "1.0", "1.0.0-preview.1", "01.0.0"):
            with self.subTest(version=version):
                self.assertIsNone(dependency_policy.pep440_version(version))


if __name__ == "__main__":
    unittest.main()
