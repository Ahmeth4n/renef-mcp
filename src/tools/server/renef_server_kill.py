import asyncio
from src.app import mcp


@mcp.tool()
async def renef_server_kill() -> str:
    """
    Kills renef_server on the connected Android device.

    Returns:
        Kill status message
    """
    # Check if running
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pidof", "renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    pid = stdout.decode().strip()

    if not pid:
        return "renef_server is not running"

    # Kill the process
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "kill", "-9", pid,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    await proc.communicate()

    # Verify it's killed
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pidof", "renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    new_pid = stdout.decode().strip()

    if not new_pid:
        return f"✓ renef_server killed (was PID: {pid})"
    else:
        return f"✗ Failed to kill renef_server (PID: {new_pid})"
