"""Windows-friendly launcher for Net Logger.

The normal CLI command is still ``net-logger serve``. This module is intended
for native Windows installer shortcuts: it starts the local Flask server, opens
the user's browser, and shows a small control window so ordinary operators do
not have to keep a PowerShell window open.
"""

from __future__ import annotations

import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from werkzeug.serving import make_server

from .app import create_app
from .config import default_database_path, load_app_settings


def browser_url(host: str, port: int) -> str:
    """Return the browser URL for a bound host and port."""
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{port}"


class NetLoggerLauncher:
    """Small desktop launcher that owns the local Net Logger server."""

    def __init__(self, host: str, port: int, database: str | Path | None = None) -> None:
        self.host = host
        self.port = int(port)
        self.url = browser_url(host, self.port)
        self.database = Path(database).expanduser() if database else default_database_path()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.app = create_app({"DATABASE": str(self.database)})
        self.server = make_server(self.host, self.port, self.app, threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, name="net-logger-server", daemon=True)

    def start(self) -> None:
        """Start the local server and open the default web browser."""
        if not self.thread.is_alive():
            self.thread.start()
            time.sleep(0.25)
        webbrowser.open(self.url)

    def open_browser(self) -> None:
        """Open the Net Logger browser UI."""
        webbrowser.open(self.url)

    def stop(self) -> None:
        """Stop the local server."""
        self.server.shutdown()


def _show_control_window(launcher: NetLoggerLauncher) -> None:
    """Show a tiny Tk control window for non-command-line Windows users."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Net Logger")
    root.geometry("420x190")
    root.resizable(False, False)

    tk.Label(root, text="Net Logger is running", font=("Segoe UI", 14, "bold")).pack(pady=(18, 6))
    tk.Label(root, text=f"Browser address: {launcher.url}").pack(pady=(0, 8))
    tk.Label(root, text="Close this window or click Quit to stop Net Logger.").pack(pady=(0, 12))

    buttons = tk.Frame(root)
    buttons.pack()

    tk.Button(buttons, text="Open Net Logger", width=18, command=launcher.open_browser).pack(side="left", padx=6)

    def quit_launcher() -> None:
        try:
            launcher.stop()
        finally:
            root.destroy()

    tk.Button(buttons, text="Quit", width=12, command=quit_launcher).pack(side="left", padx=6)

    def on_close() -> None:
        if messagebox.askokcancel("Quit Net Logger", "Stop Net Logger and close this window?"):
            quit_launcher()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


def main(argv: list[str] | None = None, **overrides: Any) -> int:
    """Launch Net Logger for a desktop shortcut.

    Keyword overrides are used by tests and by the CLI ``launch`` subcommand.
    """
    settings = load_app_settings()
    host = str(overrides.get("host") or settings["HOST"])
    port = int(overrides.get("port") or settings["PORT"])
    database = overrides.get("database") or settings.get("DATABASE")

    launcher = NetLoggerLauncher(host=host, port=port, database=database)
    launcher.start()
    _show_control_window(launcher)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
