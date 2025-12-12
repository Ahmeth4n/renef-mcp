import asyncio
from src.app import mcp


@mcp.tool()
async def adb_selinux_enable() -> str:
    """
    Sets SELinux to Enforcing mode (enabled).

    Returns:
        Result of the operation
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "setenforce", "1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace").strip()

    # Verify
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "getenforce",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    status = stdout.decode("utf-8", errors="replace").strip()

    if status == "Enforcing":
        return "✓ SELinux enabled (Enforcing)"
    else:
        return f"✗ Failed to enable SELinux. Current: {status}. {output}"
