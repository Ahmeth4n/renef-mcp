import asyncio
from src.app import mcp


@mcp.tool()
async def renef_port_forward_remove(local_port: int = 1907) -> str:
    """
    Removes a port forwarding rule.

    Args:
        local_port: Local TCP port to remove (default: 1907)

    Returns:
        Status message
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "forward", "--remove", f"tcp:{local_port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace").strip()

    if proc.returncode == 0:
        return f"✓ Port forward removed: tcp:{local_port}"
    else:
        return f"✗ Failed to remove port forward: {output}"


@mcp.tool()
async def renef_port_forward_remove_all() -> str:
    """
    Removes all port forwarding rules.

    Returns:
        Status message
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "forward", "--remove-all",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()

    if proc.returncode == 0:
        return "✓ All port forwards removed"
    else:
        output = stdout.decode("utf-8", errors="replace").strip()
        return f"✗ Failed to remove port forwards: {output}"
