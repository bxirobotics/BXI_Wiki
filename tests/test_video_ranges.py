import io
import unittest
from types import SimpleNamespace
from wsgiref.util import FileWrapper

from hooks.video_ranges import on_serve


class VideoRangeTests(unittest.TestCase):
    def setUp(self):
        self.data = bytes(range(256)) * 1024
        self.content_type = "video/mp4"
        self.status = "200 OK"
        self.server = SimpleNamespace(get_app=lambda: self.app, set_app=self.install)
        self.assertIs(on_serve(self.server, None, None), self.server)

    def install(self, app):
        self.wrapped_app = app

    def app(self, environ, start_response):
        self.stream = io.BytesIO(self.data)
        start_response(self.status, [
            ("Content-Type", self.content_type),
            ("Content-Length", str(len(self.data))),
        ])
        return FileWrapper(self.stream)

    def request(self, range_value=None, method="GET", **extra):
        environ = {"REQUEST_METHOD": method, **extra}
        if range_value is not None:
            environ["HTTP_RANGE"] = range_value
        result = {}

        def start_response(status, headers, exc_info=None):
            result.update(status=status, headers=dict(headers))

        body = self.wrapped_app(environ, start_response)
        try:
            result["body"] = b"".join(body)
        finally:
            if hasattr(body, "close"):
                body.close()
        self.assertTrue(self.stream.closed)
        return result

    def test_full_video_advertises_byte_ranges(self):
        result = self.request()
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["headers"]["Accept-Ranges"], "bytes")
        self.assertEqual(result["body"], self.data)
        self.assertNotIn("Content-Range", result["headers"])

    def test_seek_requests_return_exact_bytes(self):
        size = len(self.data)
        cases = [
            ("bytes=0-0", 0, 1),
            ("bytes=123-456", 123, 457),
            ("bytes=100-150000", 100, 150001),
            ("bytes=100000-", 100000, size),
            ("bytes=-1024", size - 1024, size),
            ("bytes=-999999", 0, size),
            ("bytes=123-999999", 123, size),
        ]
        for value, start, end in cases:
            with self.subTest(value=value):
                result = self.request(value)
                self.assertEqual(result["status"], "206 Partial Content")
                self.assertEqual(result["headers"]["Content-Range"], f"bytes {start}-{end - 1}/{size}")
                self.assertEqual(int(result["headers"]["Content-Length"]), end - start)
                self.assertEqual(result["body"], self.data[start:end])

    def test_unsatisfiable_ranges(self):
        for value in (f"bytes={len(self.data)}-", "bytes=999999-", "bytes=-0"):
            with self.subTest(value=value):
                result = self.request(value)
                self.assertEqual(result["status"], "416 Range Not Satisfiable")
                self.assertEqual(result["headers"]["Content-Range"], f"bytes */{len(self.data)}")
                self.assertEqual(result["headers"]["Content-Length"], "0")
                self.assertEqual(result["body"], b"")

    def test_invalid_and_multiple_ranges_fall_back_to_full_response(self):
        for value in ("bytes=-", "bytes=12-3", "bytes=a-b", "bytes=0-1,5-6", "items=0-1"):
            with self.subTest(value=value):
                result = self.request(value)
                self.assertEqual(result["status"], "200 OK")
                self.assertEqual(result["body"], self.data)

    def test_head_ignores_range_and_returns_no_body(self):
        result = self.request("bytes=0-1", method="HEAD")
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["headers"]["Content-Length"], str(len(self.data)))
        self.assertEqual(result["body"], b"")
        self.assertNotIn("Content-Range", result["headers"])

    def test_if_range_without_a_matching_validator_returns_full_file(self):
        result = self.request("bytes=0-1", HTTP_IF_RANGE='"old-version"')
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["body"], self.data)

    def test_empty_video_ignores_range(self):
        self.data = b""
        result = self.request("bytes=0-")
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(result["body"], b"")

    def test_non_video_responses_are_unchanged(self):
        self.content_type = "text/html"
        result = self.request("bytes=0-1")
        self.assertEqual(result["status"], "200 OK")
        self.assertNotIn("Accept-Ranges", result["headers"])
        self.assertEqual(result["body"], self.data)

    def test_errors_are_unchanged(self):
        self.status = "404 Not Found"
        result = self.request("bytes=0-1")
        self.assertEqual(result["status"], self.status)
        self.assertNotIn("Accept-Ranges", result["headers"])
        self.assertEqual(result["body"], self.data)

    def test_interrupted_stream_closes_the_file(self):
        body = self.wrapped_app(
            {"REQUEST_METHOD": "GET", "HTTP_RANGE": "bytes=100-"},
            lambda *args: None,
        )
        self.assertEqual(next(body), self.data[100:100 + 64 * 1024])
        body.close()
        self.assertTrue(self.stream.closed)


if __name__ == "__main__":
    unittest.main()
