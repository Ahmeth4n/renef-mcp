import asyncio
from src.app import mcp


@mcp.tool()
async def adb_selinux_status() -> str:
    """
    Shows the current SELinux status on the Android device.

    Returns:
        SELinux status (Enforcing/Permissive/Disabled)
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "getenforce",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    status = stdout.decode("utf-8", errors="replace").strip()

    return f"SELinux: {status}"
