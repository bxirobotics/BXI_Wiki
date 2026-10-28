"""Let browsers seek MP4 videos served by MkDocs' development server."""

import re
from wsgiref.util import FileWrapper

from mkdocs.livereload import LiveReloadServer


_original_serve_request = None


def _range_bounds(value, size):
    """Return a half-open byte interval, or ignore unsupported/invalid ranges."""
    match = re.fullmatch(r"bytes=([0-9]*)-([0-9]*)", value.strip(), re.IGNORECASE)
    if not match or not any(match.groups()):
        return None
    first, last = match.groups()
    try:
        if not first:
            return max(0, size - int(last)), size
        start = int(first)
        end = int(last) + 1 if last else size
    except ValueError:
        return None
    if last and end <= start:
        return None
    return start, min(end, size)


def _read_range(body, start, length):
    try:
        body.filelike.seek(start)
        while length:
            chunk = body.filelike.read(min(length, 64 * 1024))
            if not chunk:
                break
            length -= len(chunk)
            yield chunk
    finally:
        body.close()


def _with_video_ranges(app):
    def serve(environ, start_response):
        response = []

        def capture(status, headers, exc_info=None):
            response[:] = [status, headers, exc_info]

        body = app(environ, capture)
        status, headers, exc_info = response
        metadata = {key.lower(): value for key, value in headers}
        method = environ.get("REQUEST_METHOD", "GET")
        if (status != "200 OK" or metadata.get("content-type") != "video/mp4"
                or not isinstance(body, FileWrapper) or method not in {"GET", "HEAD"}):
            start_response(status, headers, exc_info)
            return body

        headers = [*headers, ("Accept-Ranges", "bytes")]
        if method == "HEAD":
            body.close()
            start_response(status, headers, exc_info)
            return []

        size = int(metadata["content-length"])
        # MkDocs supplies no validators, so an If-Range request needs the full file.
        bounds = None if environ.get("HTTP_IF_RANGE") or not size else _range_bounds(
            environ.get("HTTP_RANGE", ""), size
        )
        if bounds is None:
            start_response(status, headers, exc_info)
            return body

        start, end = bounds
        headers = [(key, value) for key, value in headers if key.lower() != "content-length"]
        if start >= end:
            body.close()
            headers.extend([("Content-Range", f"bytes */{size}"), ("Content-Length", "0")])
            start_response("416 Range Not Satisfiable", headers)
            return []

        headers.extend([
            ("Content-Range", f"bytes {start}-{end - 1}/{size}"),
            ("Content-Length", str(end - start)),
        ])
        start_response("206 Partial Content", headers)
        return _read_range(body, start, end - start)

    return serve


def on_startup(**kwargs):
    """Enable ranges even when serve disables live reload or uses --clean."""
    global _original_serve_request
    if _original_serve_request is not None:
        return

    original = LiveReloadServer.serve_request

    def serve_request(server, environ, start_response):
        app = original.__get__(server, type(server))
        return _with_video_ranges(app)(environ, start_response)

    # on_serve is skipped with --no-livereload. Startup runs before the server
    # captures this method as its WSGI app, including serve --clean (command=build).
    _original_serve_request = original
    LiveReloadServer.serve_request = serve_request


def on_shutdown():
    global _original_serve_request
    if _original_serve_request is not None:
        LiveReloadServer.serve_request = _original_serve_request
        _original_serve_request = None
