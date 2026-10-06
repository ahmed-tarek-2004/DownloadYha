"""
Tests for config.py and updater.py modules.
"""

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import config, dependencies, updater


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
        updater._set_last_check_time(time.time())
        self.assertFalse(updater._should_check_for_updates())

        # Checked 25 hours ago -> True
        updater._set_last_check_time(time.time() - (25 * 3600))
        self.assertTrue(updater._should_check_for_updates())

    def test_compute_sha256(self):
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_bytes(b"hello world\n")
        expected = hashlib.sha256(b"hello world\n").hexdigest()
        self.assertEqual(updater._compute_sha256(test_file), expected)

    def test_cleanup_stale_backups(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        exe = bin_dir / "downloadyha.exe"
        exe.write_bytes(b"current_exe")

        old_file1 = bin_dir / "downloadyha.exe.old"
        old_file1.write_bytes(b"old1")
        old_file2 = bin_dir / "downloadyha.old.12345.exe"
        old_file2.write_bytes(b"old2")
        tmp_file = bin_dir / "downloadyha.new.999_123.tmp.exe"
        tmp_file.write_bytes(b"tmp")

        updater.cleanup_stale_backups(exe)

        self.assertTrue(exe.exists())
        self.assertFalse(old_file1.exists())
        self.assertFalse(old_file2.exists())
        self.assertFalse(tmp_file.exists())

    def test_replace_binary_windows_success(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        target_exe = bin_dir / "downloadyha.exe"
        target_exe.write_bytes(b"version_1")

        new_binary = Path(self.test_dir) / "new_downloadyha.exe"
        new_binary.write_bytes(b"version_2")

        with patch("platform.system", return_value="Windows"):
            ok, err = updater._replace_binary(new_binary, target_exe)
            self.assertTrue(ok)
            self.assertIsNone(err)
            self.assertEqual(target_exe.read_bytes(), b"version_2")

    def test_replace_binary_windows_rollback_on_failure(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        target_exe = bin_dir / "downloadyha.exe"
        target_exe.write_bytes(b"original_content")

        new_binary = Path(self.test_dir) / "new_downloadyha.exe"
        new_binary.write_bytes(b"updated_content")

        # Simulate failure during staging -> target rename
        rename_calls = []

        def mock_rename(*args, **kwargs):
            rename_calls.append(args)
            if len(rename_calls) == 2:
                # Second rename call is staging_file -> target_exe
                raise OSError("Simulated disk error moving staging")
            # For other calls, simulate standard rename
            pass

        with patch("platform.system", return_value="Windows"), \
             patch.object(Path, "rename", side_effect=mock_rename):
            ok, err = updater._replace_binary(new_binary, target_exe)
            self.assertFalse(ok)
            self.assertIn("Original version successfully restored", err)

    def test_replace_binary_linux_success(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        target_exe = bin_dir / "downloadyha"
        target_exe.write_bytes(b"linux_v1")

        new_binary = Path(self.test_dir) / "new_downloadyha"
        new_binary.write_bytes(b"linux_v2")

        with patch("platform.system", return_value="Linux"):
            ok, err = updater._replace_binary(new_binary, target_exe)
            self.assertTrue(ok)
            self.assertIsNone(err)
            self.assertEqual(target_exe.read_bytes(), b"linux_v2")

    def test_build_artifact_name(self):
        cli_win = updater._build_artifact_name("v2.0.0", "windows-x86_64", is_gui=False)
        self.assertEqual(cli_win, "downloadyha-v2.0.0-windows-x86_64.zip")

        gui_win = updater._build_artifact_name("v2.0.0", "windows-x86_64", is_gui=True)
        self.assertEqual(gui_win, "downloadyha-gui-v2.0.0-windows-x86_64.zip")

        cli_linux = updater._build_artifact_name("v2.0.0", "linux-x86_64", is_gui=False)
        self.assertEqual(cli_linux, "downloadyha-v2.0.0-linux-x86_64.tar.gz")

        gui_linux = updater._build_artifact_name("v2.0.0", "linux-x86_64", is_gui=True)
        self.assertEqual(gui_linux, "downloadyha-gui-v2.0.0-linux-x86_64.tar.gz")

    def test_is_gui_app(self):
        gui_exe = Path("/path/to/downloadyha-gui.exe")
        cli_exe = Path("/path/to/downloadyha.exe")
        self.assertTrue(updater._is_gui_app(gui_exe))
        self.assertFalse(updater._is_gui_app(cli_exe))

    def test_safe_install_binary_success(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        target = bin_dir / "ffmpeg.exe"
        target.write_bytes(b"old_ffmpeg")

        src = Path(self.test_dir) / "new_ffmpeg.exe"
        src.write_bytes(b"new_ffmpeg")

        ok = dependencies._safe_install_binary(src, target)
        self.assertTrue(ok)
        self.assertEqual(target.read_bytes(), b"new_ffmpeg")

    def test_cleanup_stale_dependency_backups(self):
        bin_dir = Path(self.test_dir) / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        target = bin_dir / "ffmpeg.exe"
        target.write_bytes(b"ffmpeg")
        old_file = bin_dir / "ffmpeg.old.123_456.exe"
        old_file.write_bytes(b"old_ffmpeg")

        dependencies.cleanup_stale_dependency_backups(bin_dir)
        self.assertTrue(target.exists())
        self.assertFalse(old_file.exists())

    def test_perform_update_dev_mode_skips_binary_replacement(self):
        with patch.object(sys, "frozen", False, create=True), \
             patch("downloadyha.updater.init_terminal"), \
             patch("downloadyha.updater.info") as mock_info:
            ok, msg = updater.perform_update("v2.0.0")
            self.assertTrue(ok)
            self.assertIn("source code", msg)
            mock_info.assert_any_call("Downloadyha is running from source code (development mode).")


if __name__ == "__main__":
    unittest.main()
