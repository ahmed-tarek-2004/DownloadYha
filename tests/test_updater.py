"""
Tests for config.py and updater.py modules.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import config, updater


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch.object(config, "get_config_dir", return_value=Path(self.test_dir))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_default(self):
        cfg = config.load()
        self.assertIn("download_directory", cfg)
        self.assertIn("check_updates", cfg)
        self.assertTrue(cfg["check_updates"])

    def test_save_and_load(self):
        cfg = config.load()
        cfg["download_directory"] = "/custom/path"
        cfg["check_updates"] = False
        self.assertTrue(config.save(cfg))

        loaded = config.load()
        self.assertEqual(loaded["download_directory"], "/custom/path")
        self.assertEqual(loaded["check_updates"], False)

    def test_get_set_value(self):
        config.set_value("new_key", "custom_val")
        self.assertEqual(config.get("new_key"), "custom_val")


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch.object(config, "get_cache_dir", return_value=Path(self.test_dir))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_version(self):
        self.assertEqual(updater._parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(updater._parse_version("v2.1.3"), (2, 1, 3))
        self.assertEqual(updater._parse_version("invalid"), (0,))

    def test_is_newer_version(self):
        self.assertTrue(updater._is_newer_version("1.0.0", "1.0.1"))
        self.assertTrue(updater._is_newer_version("1.0.0", "2.0.0"))
        self.assertTrue(updater._is_newer_version("v1.0.0", "v1.1.0"))
        self.assertFalse(updater._is_newer_version("1.2.0", "1.2.0"))
        self.assertFalse(updater._is_newer_version("2.0.0", "1.0.0"))

    def test_last_check_time(self):
        self.assertEqual(updater._get_last_check_time(), 0.0)
        updater._set_last_check_time(12345.67)
        self.assertEqual(updater._get_last_check_time(), 12345.67)

    def test_should_check_for_updates(self):
        # Never checked -> True
        self.assertTrue(updater._should_check_for_updates())

        # Checked just now -> False
        import time
        updater._set_last_check_time(time.time())
        self.assertFalse(updater._should_check_for_updates())

        # Checked 25 hours ago -> True
        updater._set_last_check_time(time.time() - (25 * 3600))
        self.assertTrue(updater._should_check_for_updates())

    def test_compute_sha256(self):
        test_file = Path(self.test_dir) / "test.txt"
        # Use write_bytes to avoid line ending conversion on Windows
        test_file.write_bytes(b"hello world\n")
        # SHA256 of "hello world\n"
        import hashlib
        expected = hashlib.sha256(b"hello world\n").hexdigest()
        self.assertEqual(updater._compute_sha256(test_file), expected)


if __name__ == "__main__":
    unittest.main()
