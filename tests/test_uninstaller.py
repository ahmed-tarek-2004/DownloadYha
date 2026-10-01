"""
Tests for uninstaller.py module in downloadyha.
"""

import io
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import config, uninstaller


class TestUninstaller(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / "config"
        self.cache_dir = Path(self.test_dir) / "cache"
        self.logs_dir = Path(self.test_dir) / "logs"
        self.bin_dir = Path(self.test_dir) / "bin"
        self.app_data_dir = Path(self.test_dir) / "app_data"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

        self.patchers = [
            patch.object(config, "get_config_dir", return_value=self.config_dir),
            patch.object(config, "get_cache_dir", return_value=self.cache_dir),
            patch.object(config, "get_logs_dir", return_value=self.logs_dir),
            patch.object(config, "get_bin_dir", return_value=self.bin_dir),
            patch.object(config, "get_app_data_dir", return_value=self.app_data_dir),
            patch("downloadyha.uninstaller.init_terminal"),
            patch("sys.stdout", new_callable=io.StringIO),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_executable_path_not_frozen(self):
        with patch.object(sys, "frozen", False, create=True):
            path = uninstaller._get_executable_path()
            self.assertTrue(str(path).endswith("uninstaller.py"))

    def test_get_executable_path_frozen(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", "/opt/downloadyha/bin/downloadyha"):
            path = uninstaller._get_executable_path()
            self.assertEqual(path, Path("/opt/downloadyha/bin/downloadyha").resolve())

    def test_close_logging_handlers(self):
        # Create a test log file with active file handler
        test_log_file = self.logs_dir / "active.log"
        logger = logging.getLogger("downloadyha")
        handler = logging.FileHandler(str(test_log_file), mode="w", encoding="utf-8")
        logger.addHandler(handler)
        logger.info("Test active log message")

        uninstaller._close_logging_handlers()

        # The handler should be closed and detached from the logger
        self.assertNotIn(handler, logger.handlers)
        # Should be able to delete the file without permission error
        test_log_file.unlink()
        self.assertFalse(test_log_file.exists())

    def test_terminate_helper_processes(self):
        with patch("platform.system", return_value="Windows"), \
             patch("subprocess.run") as mock_run:
            uninstaller._terminate_helper_processes()
            self.assertEqual(mock_run.call_count, 3)

    def test_robust_rmtree_read_only_files(self):
        readonly_dir = Path(self.test_dir) / "readonly_folder"
        readonly_dir.mkdir(parents=True, exist_ok=True)
        ro_file = readonly_dir / "locked.txt"
        ro_file.write_text("read-only content")

        # Set read-only permissions
        os.chmod(ro_file, stat.S_IREAD)

        ok, err = uninstaller._robust_rmtree(readonly_dir)
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertFalse(readonly_dir.exists())

    def test_schedule_windows_self_delete(self):
        dummy_file = Path(self.test_dir) / "dummy.exe"
        dummy_file.write_text("binary")

        with patch("subprocess.Popen") as mock_popen:
            uninstaller._schedule_windows_self_delete(dummy_file)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "cmd.exe")
            self.assertIn("del /f /q", args[0][2])

    @patch("downloadyha.uninstaller.prompt_confirm", return_value=False)
    def test_uninstall_canceled_by_user(self, mock_confirm):
        result = uninstaller.uninstall()
        self.assertFalse(result)
        # Verify directories are not deleted
        self.assertTrue(self.config_dir.exists())
        self.assertTrue(self.cache_dir.exists())
        self.assertTrue(self.logs_dir.exists())

    @patch("downloadyha.uninstaller._uninstall_pip_package", return_value=(True, None))
    @patch("downloadyha.uninstaller._remove_standalone_installation", return_value=[])
    @patch("downloadyha.uninstaller.prompt_confirm", return_value=True)
    def test_uninstall_success_dev_mode(self, mock_confirm, mock_standalone, mock_pip):
        with patch.object(sys, "frozen", False, create=True):
            result = uninstaller.uninstall()
            self.assertTrue(result)
            self.assertFalse(self.config_dir.exists())
            self.assertFalse(self.cache_dir.exists())
            self.assertFalse(self.logs_dir.exists())
            self.assertFalse(self.bin_dir.exists())
            self.assertFalse(self.app_data_dir.exists())
            mock_pip.assert_called_once()

    @patch("downloadyha.uninstaller.prompt_confirm", return_value=True)
    def test_uninstall_success_frozen_posix(self, mock_confirm):
        fake_exe = Path(self.test_dir) / "downloadyha_app"
        fake_exe.write_text("binary")

        with patch.object(sys, "frozen", True, create=True), \
             patch("downloadyha.uninstaller._get_executable_path", return_value=fake_exe), \
             patch("platform.system", return_value="Linux"):
            result = uninstaller.uninstall()
            self.assertTrue(result)
            self.assertFalse(fake_exe.exists())

    @patch("downloadyha.uninstaller.prompt_confirm", return_value=True)
    def test_uninstall_success_frozen_windows(self, mock_confirm):
        fake_exe = Path(self.test_dir) / "downloadyha.exe"
        fake_exe.write_text("windows_binary")

        with patch.object(sys, "frozen", True, create=True), \
             patch("downloadyha.uninstaller._get_executable_path", return_value=fake_exe), \
             patch("platform.system", return_value="Windows"), \
             patch("downloadyha.uninstaller._schedule_windows_self_delete") as mock_sched:
            result = uninstaller.uninstall()
            self.assertTrue(result)
            # The original target path downloadyha.exe was renamed
            self.assertFalse(fake_exe.exists())
            mock_sched.assert_called_once()

    @patch("downloadyha.uninstaller.prompt_confirm", return_value=True)
    def test_uninstall_handles_os_error_gracefully(self, mock_confirm):
        with patch("downloadyha.uninstaller._robust_rmtree", return_value=(False, "Simulated Permission Denied")):
            result = uninstaller.uninstall()
            self.assertFalse(result)

    def test_uninstall_pip_package(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok, err = uninstaller._uninstall_pip_package()
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_remove_standalone_installation(self):
        with patch("platform.system", return_value="Windows"), \
             patch.dict(os.environ, {"LOCALAPPDATA": self.test_dir}), \
             patch("downloadyha.uninstaller._remove_path_from_windows_registry"):
            prog_dir = Path(self.test_dir) / "Programs" / "Downloadyha"
            prog_dir.mkdir(parents=True, exist_ok=True)
            dummy_exe = prog_dir / "downloadyha.exe"
            dummy_exe.write_text("binary")

            removed = uninstaller._remove_standalone_installation()
            self.assertIn(str(prog_dir), removed)
            self.assertFalse(prog_dir.exists())

    @patch("downloadyha.uninstaller.uninstall", return_value=True)
    def test_handle_uninstall_command(self, mock_uninstall):
        uninstaller.handle_uninstall_command()
        mock_uninstall.assert_called_once()


if __name__ == "__main__":
    unittest.main()
