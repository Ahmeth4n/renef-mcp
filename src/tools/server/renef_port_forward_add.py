import asyncio
from src.app import mcp


@mcp.tool()
async def renef_port_forward_add(local_port: int = 1907, remote: str = "localabstract:com.android.internal.os.RuntimeInit") -> str:
    """
    Adds a port forwarding rule for renef.

    Args:
        local_port: Local TCP port (default: 1907)
        remote: Remote address (default: localabstract:com.android.internal.os.RuntimeInit)

    Returns:
        Status message
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "forward", f"tcp:{local_port}", remote,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace").strip()

    if proc.returncode == 0:
        return f"✓ Port forward added: tcp:{local_port} -> {remote}"
    else:
        return f"✗ Failed to add port forward: {output}"
