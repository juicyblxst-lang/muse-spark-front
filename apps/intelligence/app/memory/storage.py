from __future__ import annotations

import os
from pathlib import Path


class MemoryStoreUnavailable(RuntimeError):
    """Raised when the configured persistent memory store cannot be opened."""


def verify_memory_store(path: str | Path) -> Path:
    """Create/check the configured directory and verify it is writable.

    The actual Sibyl client opens the SQLite file. This check intentionally does
    not create a replacement database or migrate Sibyl's storage engine.
    """
    root = Path(path).expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir() or not os.access(root, os.W_OK):
            raise MemoryStoreUnavailable(f"memory store is not writable: {root}")
        probe = root / ".muse-write-test"
        probe.write_bytes(b"")
        probe.unlink()
    except (OSError, MemoryStoreUnavailable) as exc:
        if isinstance(exc, MemoryStoreUnavailable):
            raise
        raise MemoryStoreUnavailable(f"memory store cannot be opened: {root}") from exc
    return root
