"""PyInstaller entry point for the Windows Net Logger desktop launcher."""

from net_logger import windows_launcher


if __name__ == "__main__":
    raise SystemExit(windows_launcher.main())
