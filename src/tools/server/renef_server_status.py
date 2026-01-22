import asyncio
from src.app import mcp


@mcp.tool()
async def renef_server_status() -> str:
    """
    Checks if renef_server and libagent.so are deployed on the device,
    and whether renef_server is currently running.

    Returns:
        Status report of renef deployment and server state
    """
    results = []

    # Check if renef_server exists
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "test", "-f", "/data/local/tmp/renef_server", "&&", "echo", "exists",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    server_exists = "exists" in stdout.decode()
    results.append(f"renef_server: {'✓ deployed' if server_exists else '✗ not found'}")

    # Check if libagent.so exists
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "test", "-f", "/sdcard/Android/.cache", "&&", "echo", "exists",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    agent_exists = "exists" in stdout.decode()
    results.append(f"libagent.so:  {'✓ deployed' if agent_exists else '✗ not found'}")

    # Check if renef_server is running
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pidof", "renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    pid = stdout.decode().strip()
    if pid:
        results.append(f"renef_server: ✓ running (PID: {pid})")
    else:
        results.append("renef_server: ✗ not running")

    return "\n".join(results)
