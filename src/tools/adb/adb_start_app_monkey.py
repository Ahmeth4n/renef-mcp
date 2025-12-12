import asyncio
from src.app import mcp


@mcp.tool()
async def adb_start_app_monkey(package_name: str) -> str:
    """
    Starts an Android app on the connected device using 'monkey' command.
    Useful for simulating user interaction to launch an app.

    Args:
        package_name: The package name of the app (e.g., com.android.settings)

    Returns:
        ADB command output
    """
    # Use monkey to launch the main activity
    # --pct-syskeys 0 is needed for emulators without physical keys
    cmd = ["adb", "shell", "monkey", "-p", package_name, "-c",
           "android.intent.category.LAUNCHER", "--pct-syskeys", "0", "1"]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()
