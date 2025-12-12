import asyncio
from src.app import mcp


@mcp.tool()
async def adb_stop_app_am(package_name: str) -> str:
    """
    Force stops an Android app on the connected device using 'am force-stop'.

    Args:
        package_name: The package name of the app (e.g., com.android.settings)

    Returns:
        ADB command output
    """
    cmd = ["adb", "shell", "am", "force-stop", package_name]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip() or "App stopped successfully"
