"""LifeDiary desktop launcher.

Boots Django + waitress in a daemon thread and renders the UI through
pywebview. Designed to work both in a local dev run and inside a
PyInstaller bundle (``sys._MEIPASS``).
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path


def _bootstrap_path() -> None:
    if hasattr(sys, "_MEIPASS"):
        sys.path.insert(0, sys._MEIPASS)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> None:
    _bootstrap_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lifeDiary.settings.desktop")

    import django

    django.setup()

    from django.core.management import call_command

    call_command("migrate", "--noinput", verbosity=0)
    if not hasattr(sys, "_MEIPASS"):
        call_command("collectstatic", "--noinput", verbosity=0)

    from django.core.wsgi import get_wsgi_application
    from waitress import serve
    import webview

    app = get_wsgi_application()
    port = _find_free_port()

    thread = threading.Thread(
        target=serve,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": port, "threads": 4, "_quiet": True},
        daemon=True,
    )
    thread.start()

    if not _wait_for_server(port):
        sys.exit("LifeDiary server failed to start within 10 seconds")

    webview.create_window(
        "LifeDiary",
        f"http://127.0.0.1:{port}",
        width=1200,
        height=800,
    )
    webview.start()


if __name__ == "__main__":
    main()
