"""
Tests for downloadyha/cli.py module.

Tests CLI interactive workflows, argument parsing, dependency verification,
subcommand routing, and Desktop GUI launcher dispatch logic.
"""

import io
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import __version__, cli


class TestCLIFolderSelection(unittest.TestCase):
    """Test destination directory selection logic."""

    @patch("downloadyha.cli.prompt_input")
    @patch("os.makedirs")
    def test_choose_download_folder_success(self, mock_makedirs, mock_prompt):
        mock_prompt.return_value = '"C:/Downloads/YouTube"'
        path = cli.choose_download_folder()
        self.assertEqual(path, "C:/Downloads/YouTube")
        mock_makedirs.assert_called_once_with("C:/Downloads/YouTube", exist_ok=True)

    @patch("downloadyha.cli.prompt_input")
    @patch("os.makedirs", side_effect=OSError("Permission denied"))
    @patch("downloadyha.cli.error")
    def test_choose_download_folder_failure(self, mock_error, mock_makedirs, mock_prompt):
        mock_prompt.return_value = "/root/protected"
        path = cli.choose_download_folder()
        self.assertIsNone(path)
        mock_error.assert_called_once()


class TestCLIArgumentParser(unittest.TestCase):
    """Test CLI argument parser configuration."""

    def test_create_parser(self):
        parser = cli.create_parser()
        args = parser.parse_args(["--verify", "--verbose"])
        self.assertTrue(args.verify)
        self.assertTrue(args.verbose)


class TestCLIGUIDispatch(unittest.TestCase):
    """Test Desktop GUI launching dispatch logic in handle_gui_command()."""

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.info")
    @patch("subprocess.Popen")
    @patch("os.access", return_value=True)
    @patch.object(Path, "exists", return_value=True)
    def test_handle_gui_command_sibling_binary_windows(
        self, mock_exists, mock_access, mock_popen, mock_info, mock_init
    ):
        """Test launching sibling downloadyha-gui binary on Windows."""
        with patch("sys.platform", "win32"):
            cli.handle_gui_command()
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertTrue(str(args[0][0]).endswith("downloadyha-gui.exe"))
            self.assertIn("creationflags", kwargs)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.info")
    @patch("subprocess.Popen")
    @patch("os.access", return_value=True)
    @patch.object(Path, "exists", return_value=True)
    def test_handle_gui_command_sibling_binary_posix(
        self, mock_exists, mock_access, mock_popen, mock_info, mock_init
    ):
        """Test launching sibling downloadyha-gui binary on POSIX."""
        with patch("sys.platform", "linux"):
            cli.handle_gui_command()
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertTrue(str(args[0][0]).endswith("downloadyha-gui"))
            self.assertTrue(kwargs.get("start_new_session"))

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.info")
    @patch("subprocess.Popen")
    @patch("shutil.which", return_value="/usr/local/bin/downloadyha-gui")
    @patch.object(Path, "exists", return_value=False)
    def test_handle_gui_command_path_binary(
        self, mock_exists, mock_which, mock_popen, mock_info, mock_init
    ):
        """Test launching GUI binary found in PATH."""
        with patch("sys.platform", "linux"):
            cli.handle_gui_command()
            mock_popen.assert_called_once_with(
                ["/usr/local/bin/downloadyha-gui"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    @patch("downloadyha.cli.init_terminal")
    @patch("shutil.which", return_value=None)
    @patch.object(Path, "exists", return_value=False)
    def test_handle_gui_command_modern_ctk_gui_fallback(
        self, mock_exists, mock_which, mock_init
    ):
        """Test fallback to downloadyha_gui.app.main when standalone binary is not found."""
        mock_modern_main = MagicMock()
        with patch.dict("sys.modules", {"downloadyha_gui.app": MagicMock(main=mock_modern_main)}):
            cli.handle_gui_command()
            mock_modern_main.assert_called_once()

    @patch("downloadyha.cli.init_terminal")
    @patch("shutil.which", return_value=None)
    @patch.object(Path, "exists", return_value=False)
    def test_handle_gui_command_tkinter_gui_fallback(
        self, mock_exists, mock_which, mock_init
    ):
        """Test fallback to downloadyha.gui.launch_gui when downloadyha_gui is unavailable."""
        mock_tkinter_launch = MagicMock()
        # Simulate downloadyha_gui not found, but downloadyha.gui available
        with patch.dict("sys.modules", {
            "downloadyha_gui": None,
            "downloadyha_gui.app": None,
            "downloadyha.gui": MagicMock(launch_gui=mock_tkinter_launch)
        }):
            cli.handle_gui_command()
            mock_tkinter_launch.assert_called_once()

    @patch("downloadyha.cli.init_terminal")
    @patch("shutil.which", return_value=None)
    @patch.object(Path, "exists", return_value=False)
    def test_handle_gui_command_no_gui_available(
        self, mock_exists, mock_which, mock_init
    ):
        """Test helpful error message and exit(1) when no GUI modules are available."""
        with patch.dict("sys.modules", {
            "downloadyha_gui": None,
            "downloadyha_gui.app": None,
            "downloadyha.gui": None,
        }):
            with self.assertRaises(SystemExit) as cm:
                cli.handle_gui_command()
            self.assertEqual(cm.exception.code, 1)


class TestCLIInteractiveWorkflows(unittest.TestCase):
    """Test interactive download workflows in run_download_interactive()."""

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=False)
    def test_run_download_interactive_missing_deps(
        self, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 1)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="")
    def test_run_download_interactive_empty_url(
        self, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 1)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/watch?v=123")
    @patch("downloadyha.cli.choose_download_folder", return_value=None)
    def test_run_download_interactive_canceled_folder(
        self, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 1)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/watch?v=123")
    @patch("downloadyha.cli.choose_download_folder", return_value="/tmp/downloads")
    @patch("downloadyha.cli.get_media_info", return_value=None)
    def test_run_download_interactive_metadata_fetch_failure(
        self, mock_info, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 1)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/watch?v=123")
    @patch("downloadyha.cli.choose_download_folder", return_value="/tmp/downloads")
    @patch("downloadyha.cli.get_media_info", return_value={"title": "Song", "formats": []})
    @patch("downloadyha.cli.prompt_choice", side_effect=["audio", "320"])
    @patch("downloadyha.cli.download_audio", return_value=True)
    def test_run_download_interactive_single_audio_success(
        self, mock_dl, mock_choice, mock_info, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 0)
        mock_dl.assert_called_once_with("https://youtube.com/watch?v=123", "/tmp/downloads", "320")

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/watch?v=123")
    @patch("downloadyha.cli.choose_download_folder", return_value="/tmp/downloads")
    @patch("downloadyha.cli.get_media_info", return_value={"title": "Video", "formats": [{"height": 1080}]})
    @patch("downloadyha.cli.prompt_choice", side_effect=["video", "1080"])
    @patch("downloadyha.cli.download_video", return_value=True)
    def test_run_download_interactive_single_video_success(
        self, mock_dl, mock_choice, mock_info, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 0)
        mock_dl.assert_called_once_with("https://youtube.com/watch?v=123", "/tmp/downloads", 1080)

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/playlist?list=PL123")
    @patch("downloadyha.cli.choose_download_folder", return_value="/tmp/downloads")
    @patch("downloadyha.cli.get_media_info", return_value={"_type": "playlist", "title": "My Playlist", "entries": [{"id": "1"}]})
    @patch("downloadyha.cli.prompt_choice", side_effect=["video", "1080"])
    @patch("downloadyha.cli.download_playlist", return_value={"success": True, "output_dir": "/tmp/downloads/My Playlist"})
    def test_run_download_interactive_playlist_video_success(
        self, mock_dl, mock_choice, mock_info, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 0)
        mock_dl.assert_called_once_with(
            url="https://youtube.com/playlist?list=PL123",
            download_path="/tmp/downloads",
            media_type="video",
            quality="1080"
        )

    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    @patch("downloadyha.cli.updater.notify_update_available")
    @patch("downloadyha.cli.check_dependencies", return_value=True)
    @patch("downloadyha.cli.prompt_input", return_value="https://youtube.com/playlist?list=PL123")
    @patch("downloadyha.cli.choose_download_folder", return_value="/tmp/downloads")
    @patch("downloadyha.cli.get_media_info", return_value={"_type": "playlist", "title": "My Playlist", "entries": [{"id": "1"}]})
    @patch("downloadyha.cli.prompt_choice", side_effect=["audio", "320"])
    @patch("downloadyha.cli.download_playlist", return_value={"success": False, "error": "Some items failed"})
    def test_run_download_interactive_playlist_audio_failure(
        self, mock_dl, mock_choice, mock_info, mock_folder, mock_prompt, mock_deps, mock_update, mock_banner, mock_init
    ):
        result = cli.run_download_interactive()
        self.assertEqual(result, 1)


class TestCLISubcommands(unittest.TestCase):
    """Test CLI main() subcommand routing."""

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.handle_gui_command")
    def test_main_gui_command(self, mock_gui, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "gui"]):
            cli.main()
            mock_gui.assert_called_once()

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.updater.handle_update_command")
    def test_main_update_command(self, mock_update, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "update"]):
            cli.main()
            mock_update.assert_called_once()

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.repair_dependencies", return_value=True)
    def test_main_repair_success(self, mock_repair, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "repair"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)
            mock_repair.assert_called_once()

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.repair_dependencies", return_value=False)
    def test_main_repair_failure(self, mock_repair, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "repair"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 1)

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.uninstaller.handle_uninstall_command")
    def test_main_uninstall_command(self, mock_uninstall, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "uninstall"]):
            cli.main()
            mock_uninstall.assert_called_once()

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.verify_dependencies", return_value=True)
    def test_main_verify_success(self, mock_verify, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "--verify"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 0)

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.verify_dependencies", return_value=False)
    def test_main_verify_failure(self, mock_verify, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "--verify"]):
            with self.assertRaises(SystemExit) as cm:
                cli.main()
            self.assertEqual(cm.exception.code, 1)

    @patch("downloadyha.cli.setup_logging")
    def test_main_version_command(self, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "--version"]), \
             patch("builtins.print") as mock_print:
            cli.main()
            mock_print.assert_called_with(f"Downloadyha {__version__}")

    @patch("downloadyha.cli.setup_logging")
    @patch("downloadyha.cli.init_terminal")
    @patch("downloadyha.cli.print_banner")
    def test_main_help_command(self, mock_banner, mock_init, mock_log):
        with patch.object(sys, "argv", ["downloadyha", "--help"]):
            cli.main()
            mock_banner.assert_called_once()


if __name__ == "__main__":
    unittest.main()
