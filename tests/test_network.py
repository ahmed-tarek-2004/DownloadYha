"""
Unit tests for downloadyha.network module.
"""

import os
import ssl
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from downloadyha.network import (
    _find_ca_bundle,
    _is_ssl_verification_error,
    configure_ssl_environment,
    download_url_to_file,
    get_ssl_context,
    open_url,
)


class TestNetworkModule(unittest.TestCase):
    """Tests for SSL and network helpers."""

    def test_find_ca_bundle_returns_string_or_none(self):
        bundle = _find_ca_bundle()
        if bundle is not None:
            self.assertIsInstance(bundle, str)
            self.assertTrue(os.path.exists(bundle))

    def test_configure_ssl_environment(self):
        configure_ssl_environment()
        bundle = _find_ca_bundle()
        if bundle:
            self.assertIn("SSL_CERT_FILE", os.environ)
            self.assertIn("REQUESTS_CA_BUNDLE", os.environ)

    def test_get_ssl_context_verified(self):
        ctx = get_ssl_context(verify=True)
        self.assertIsInstance(ctx, ssl.SSLContext)
        self.assertIsNotNone(ctx)

    def test_get_ssl_context_unverified(self):
        ctx = get_ssl_context(verify=False)
        self.assertIsInstance(ctx, ssl.SSLContext)
        self.assertFalse(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)

    def test_is_ssl_verification_error(self):
        self.assertTrue(_is_ssl_verification_error(Exception("certificate verify failed: unable to get local issuer certificate")))
        self.assertTrue(_is_ssl_verification_error(Exception("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")))
        self.assertFalse(_is_ssl_verification_error(Exception("Connection timed out")))
        self.assertFalse(_is_ssl_verification_error(Exception("404 Not Found")))

    @patch("urllib.request.urlopen")
    def test_open_url_success_verified(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with open_url("https://example.com/test", timeout=10) as resp:
            self.assertEqual(resp, mock_resp)

        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_open_url_fallback_on_ssl_error(self, mock_urlopen):
        ssl_err = urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)")
        mock_fallback_resp = MagicMock()
        mock_fallback_resp.__enter__.return_value = mock_fallback_resp

        # First call raises SSL error, second call succeeds with unverified context
        mock_urlopen.side_effect = [ssl_err, mock_fallback_resp]

        with open_url("https://example.com/test", timeout=10) as resp:
            self.assertEqual(resp, mock_fallback_resp)

        self.assertEqual(mock_urlopen.call_count, 2)
        # Verify second call used unverified context
        second_call_kwargs = mock_urlopen.call_args_list[1][1]
        self.assertIn("context", second_call_kwargs)
        ctx = second_call_kwargs["context"]
        self.assertFalse(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)

    @patch("downloadyha.network.open_url")
    def test_download_url_to_file_success(self, mock_open_url):
        mock_resp = MagicMock()
        mock_resp.read.side_effect = [b"test data chunk", b""]
        mock_resp.__enter__.return_value = mock_resp
        mock_open_url.return_value = mock_resp

        with TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "output.bin"
            download_url_to_file("https://example.com/file.bin", dest)
            self.assertTrue(dest.exists())
            self.assertEqual(dest.read_bytes(), b"test data chunk")

    @patch("downloadyha.network.open_url")
    def test_download_url_to_file_stdout_none(self, mock_open_url):
        mock_resp = MagicMock()
        mock_resp.headers.get.return_value = "100"
        mock_resp.read.side_effect = [b"test data chunk", b""]
        mock_resp.__enter__.return_value = mock_resp
        mock_open_url.return_value = mock_resp

        with TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "output.bin"
            with patch("sys.stdout", None):
                download_url_to_file("https://example.com/file.bin", dest, show_progress=True)
                self.assertTrue(dest.exists())
                self.assertEqual(dest.read_bytes(), b"test data chunk")


if __name__ == "__main__":
    unittest.main()
