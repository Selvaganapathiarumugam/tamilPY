"""SSE helpers for streaming CLI subprocess output."""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import AsyncIterator
from pathlib import Path


async def stream_command(
    args: list[str],
    *,
    cwd: Path,
) -> AsyncIterator[str]:
    """
    Run a subprocess and yield SSE ``data:`` lines with JSON payloads.

    Events::

        {"type": "stdout"|"stderr"|"exit", "text"?: str, "code"?: int}
    """
    command = [sys.executable, "-m", "tpy.cli", *args]
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _pump(stream: asyncio.StreamReader, kind: str) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace")
            queue.put_nowait({"type": kind, "text": text})

    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def _wait() -> None:
        await asyncio.gather(
            _pump(process.stdout, "stdout"),  # type: ignore[arg-type]
            _pump(process.stderr, "stderr"),  # type: ignore[arg-type]
        )
        code = await process.wait()
        queue.put_nowait({"type": "exit", "code": code})
        queue.put_nowait(None)

    waiter = asyncio.create_task(_wait())
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
    finally:
        if not waiter.done():
            waiter.cancel()
