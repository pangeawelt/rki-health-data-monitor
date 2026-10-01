import socket

import requests

from src.api.embedded import start_embedded_api


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_api_is_started_in_the_background_and_reused(rki_db) -> None:
    base_url = f"http://127.0.0.1:{_free_port()}"

    assert start_embedded_api(base_url, timeout=60) is True
    assert requests.get(f"{base_url}/health", timeout=5).json()["status"] == "ok"
    assert requests.get(f"{base_url}/api/status", timeout=5).json()["total_rows"] > 0

    assert start_embedded_api(base_url, timeout=5) is True  # already running: nothing is started a second time


def test_remote_addresses_are_never_started() -> None:
    assert start_embedded_api("http://example.invalid:8000", timeout=1) is False


def test_a_port_that_is_taken_by_something_else_gives_up_quickly() -> None:
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        assert start_embedded_api(f"http://127.0.0.1:{port}", timeout=30) is False
