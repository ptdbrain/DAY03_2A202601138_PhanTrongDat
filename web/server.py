"""Local web server for the DAY03 course assistant."""

import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

WEB_DIR = Path(__file__).resolve().parent
PROJECT_DIR = WEB_DIR.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from app import run_react_agent  # noqa: E402
from providers import get_llm_provider  # noqa: E402


SUPPORTED_TERMS = (
    "khóa học",
    "khoá học",
    "python",
    "machine learning",
    "data analysis",
    "data analytics",
    "học online",
    "học offline",
    "học trực tuyến",
    "lộ trình học",
    "phương pháp học",
    "coursera",
    "udemy",
    "youtube",
)

COURSE_CONTEXT_TERMS = (
    "khóa học",
    "khoá học",
    "course",
    "python",
    "machine learning",
    "data analysis",
    "data analytics",
    "coursera",
    "udemy",
    "youtube",
)

OUT_OF_SCOPE_MESSAGE = (
    "Tôi chỉ hỗ trợ tư vấn khóa học, Python, Machine Learning, Data Analysis, "
    "review khóa học và phương pháp học online/offline."
)


def is_in_scope(query: str) -> bool:
    """Return True only for topics supported by this course assistant."""
    if not isinstance(query, str):
        return False
    normalized = " ".join(query.lower().split())
    if not normalized:
        return False
    if any(term in normalized for term in SUPPORTED_TERMS):
        return True
    has_course_context = any(term in normalized for term in COURSE_CONTEXT_TERMS)
    has_review_request = "review" in normalized or "đánh giá" in normalized
    return has_course_context and has_review_request


def build_chat_response(query: str) -> dict:
    """Apply the scope boundary, then delegate in-scope work to the existing agent."""
    if not is_in_scope(query):
        return {
            "answer": OUT_OF_SCOPE_MESSAGE,
            "termination": "out_of_scope",
            "tool_calls": [],
            "in_scope": False,
        }

    provider = get_llm_provider("mock")
    result = run_react_agent(query.strip(), provider, verbose=False)
    return {
        "answer": result["answer"],
        "termination": result["termination"],
        "tool_calls": result["tool_calls"],
        "in_scope": True,
    }


class ChatHandler(BaseHTTPRequestHandler):
    """Serve the static UI and the JSON chat endpoint."""

    server_version = "DAY03Chat/1.0"

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename: str) -> None:
        target = (WEB_DIR / filename).resolve()
        if WEB_DIR not in target.parents or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        filename = "index.html" if path == "/" else path.lstrip("/")
        if filename in {"index.html", "styles.css", "app.js"}:
            self._send_file(filename)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/chat":
            self._send_json({"error": "Endpoint không tồn tại."}, HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20_000:
                raise ValueError("Kích thước request không hợp lệ.")
            raw_body = self.rfile.read(length)
            data = json.loads(raw_body.decode("utf-8"))
            query = data.get("query") if isinstance(data, dict) else None
            if not isinstance(query, str) or not query.strip():
                raise ValueError("Vui lòng nhập câu hỏi.")
            self._send_json(build_chat_response(query.strip()))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self._send_json({"error": "Không thể xử lý yêu cầu lúc này."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args) -> None:
        """Keep local demo output concise."""
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = ThreadingHTTPServer((host, port), ChatHandler)
    print(f"DAY03 Chat đang chạy tại http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng DAY03 Chat.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.getenv("DAY03_WEB_PORT", "8000"))
    serve(port=port)
