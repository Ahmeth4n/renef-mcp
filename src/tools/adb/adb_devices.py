import asyncio
from src.app import mcp


@mcp.tool()
async def adb_devices() -> str:
    """
    Lists connected Android devices.

    Returns:
        ADB devices output
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "devices", "-l",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()
