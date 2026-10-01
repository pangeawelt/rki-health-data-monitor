"""Run the API inside the current process.

Some hosts (for example Streamlit Community Cloud) start only the Streamlit process. The dashboard then calls this
function to bring up the API in a background thread, so the usual UI -> API -> database layering stays intact.
"""
import threading
import time
from urllib.parse import urlparse

import requests
import uvicorn

LOCAL_HOSTS = {"127.0.0.1", "localhost"}
POLL_SECONDS = 0.5

_start_lock = threading.Lock()


def _is_up(base_url: str) -> bool:
    try:
        return requests.get(f"{base_url}/health", timeout=2).ok
    except requests.RequestException:
        return False


def _serve(server: uvicorn.Server) -> None:
    try:
        server.run()
    except SystemExit:  # uvicorn exits when the port cannot be bound; the caller notices the dead thread
        pass


def start_embedded_api(base_url: str, timeout: float = 120.0) -> bool:
    """Make sure an API answers at ``base_url``; start one in a background thread if none does yet.

    Only local addresses are started. Returns whether the API is reachable afterwards. The first start of an empty
    database includes the RKI download, hence the generous default timeout.
    """
    base_url = base_url.rstrip("/")
    parsed = urlparse(base_url)
    with _start_lock:
        if _is_up(base_url):
            return True
        if parsed.hostname not in LOCAL_HOSTS or not parsed.port:
            return False
        server = uvicorn.Server(uvicorn.Config("src.api.app:app", host="127.0.0.1", port=parsed.port, log_level="warning"))
        thread = threading.Thread(target=_serve, args=(server,), name="embedded-api", daemon=True)
        thread.start()

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and thread.is_alive():  # a dead thread means the port was not available
        if _is_up(base_url):
            return True
        time.sleep(POLL_SECONDS)
    return _is_up(base_url)
