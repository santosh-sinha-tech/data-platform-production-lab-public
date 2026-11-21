"""Pinned MCP SDK adapter. Launch configuration is selected by the lab host."""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connect(root: Path, ledger: Path, variant="normal"):
    script = root / "servers" / "operations.py"
    if variant == "unavailable":
        script = script.with_name("unavailable.py")
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(script), str(root / "config/policy.json"), str(ledger), variant],
    )
    with open(os.devnull, "w") as suppressed:
        async with stdio_client(params, errlog=suppressed) as (read, write):
            async with ClientSession(read, write) as session:
                async with asyncio.timeout(3):
                    initialized = await session.initialize()
                yield initialized, session
