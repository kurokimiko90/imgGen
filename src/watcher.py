"""
watcher.py - Folder monitoring for automatic card generation.

Watches a directory for new .txt, .md, or .url files and triggers
the imgGen pipeline for each detected file.
"""

import logging
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger("imggen.watcher")

WATCH_EXTENSIONS = {".txt", ".md", ".url"}
DEBOUNCE_SECONDS = 2.0


class _DebouncedHandler:
    """Tracks file events with a debounce window."""

    def __init__(
        self,
        callback: Callable[[Path], None],
        debounce: float = DEBOUNCE_SECONDS,
    ) -> None:
        self._callback = callback
        self._debounce = debounce
        self._pending: dict[str, float] = {}

    def on_file_event(self, path: Path) -> None:
        """Record a file event (created or modified)."""
        if path.suffix.lower() not in WATCH_EXTENSIONS:
            return
        self._pending[str(path)] = time.monotonic()

    def flush(self) -> None:
        """Process any events past the debounce window."""
        now = time.monotonic()
        ready = [
            p for p, t in self._pending.items()
            if now - t >= self._debounce
        ]
        for p in ready:
            del self._pending[p]
            path = Path(p)
            if path.exists():
                try:
                    self._callback(path)
                except Exception:
                    logger.exception("Error processing %s", path)


def _read_file_content(path: Path) -> str:
    """Read file content, handling .url files specially."""
    if path.suffix.lower() == ".url":
        # .url file contains a single URL — fetch it
        url = path.read_text(encoding="utf-8").strip()
        if not url:
            raise ValueError(f"Empty .url file: {path}")
        from src.fetcher import fetch_url_content
        return fetch_url_content(url)

    return path.read_text(encoding="utf-8")


def watch_directory(
    directory: Path,
    callback: Callable[[Path], None],
    *,
    poll_interval: float = 1.0,
) -> None:
    """Watch a directory for new/modified files and invoke callback.

    This function blocks indefinitely. Uses watchdog if available,
    falls back to polling otherwise.

    Args:
        directory: Directory to watch.
        callback: Called with the Path of each detected file.
        poll_interval: Seconds between poll cycles (fallback mode).
    """
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    handler = _DebouncedHandler(callback)

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

        class _WatchdogHandler(FileSystemEventHandler):
            def on_created(self, event: FileCreatedEvent) -> None:
                if not event.is_directory:
                    handler.on_file_event(Path(event.src_path))

            def on_modified(self, event: FileModifiedEvent) -> None:
                if not event.is_directory:
                    handler.on_file_event(Path(event.src_path))

        observer = Observer()
        observer.schedule(_WatchdogHandler(), str(directory), recursive=False)
        observer.start()
        logger.info("Watching %s (watchdog mode)", directory)

        try:
            while True:
                handler.flush()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    except ImportError:
        # Fallback: simple polling
        logger.info("Watching %s (polling mode, watchdog not installed)", directory)
        seen: dict[str, float] = {}

        try:
            while True:
                for p in directory.iterdir():
                    if p.is_file() and p.suffix.lower() in WATCH_EXTENSIONS:
                        mtime = p.stat().st_mtime
                        key = str(p)
                        if key not in seen or seen[key] < mtime:
                            seen[key] = mtime
                            handler.on_file_event(p)
                handler.flush()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            pass

    logger.info("Watcher stopped.")
