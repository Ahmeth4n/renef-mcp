import asyncio
from src.app import mcp


@mcp.tool()
async def renef_server_start() -> str:
    """
    Starts renef_server on the connected Android device.

    Also sets up port forwarding (tcp:1907).

    Returns:
        Start status message
    """
    # Check if already running
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pidof", "renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    pid = stdout.decode().strip()

    if pid:
        return f"renef_server already running (PID: {pid})"

    # Setup port forwarding
    proc = await asyncio.create_subprocess_exec(
        "adb", "forward", "tcp:1907", "localabstract:com.android.internal.os.RuntimeInit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    await proc.communicate()

    # Start server in background
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "nohup", "/data/local/tmp/renef_server", ">", "/dev/null", "2>&1", "&",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    await proc.communicate()

    # Wait a bit and check if started
    await asyncio.sleep(0.5)

    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pidof", "renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    pid = stdout.decode().strip()

    if pid:
        return f"✓ renef_server started (PID: {pid})"
    else:
        return "✗ Failed to start renef_server"
