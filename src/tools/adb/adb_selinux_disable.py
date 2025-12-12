import asyncio
from src.app import mcp


@mcp.tool()
async def adb_selinux_disable() -> str:
    """
    Sets SELinux to Permissive mode (disabled enforcement).

    Returns:
        Result of the operation
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "setenforce", "0",
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

    if status == "Permissive":
        return "✓ SELinux disabled (Permissive)"
    else:
        return f"✗ Failed to disable SELinux. Current: {status}. {output}"
