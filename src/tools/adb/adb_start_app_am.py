import asyncio
from src.app import mcp


@mcp.tool()
async def adb_start_app_am(package_name: str, activity: str = "") -> str:
    """
    Starts an Android app on the connected device using 'am start'.

    Args:
        package_name: The package name of the app (e.g., com.android.settings)
        activity: Optional activity name. If not provided, launches the main/launcher activity.

    Returns:
        ADB command output
    """
    if activity:
        component = f"{package_name}/{activity}"
        cmd = ["adb", "shell", "am", "start", "-n", component]
    else:
        # Launch main activity using am start with action MAIN and category LAUNCHER
        cmd = ["adb", "shell", "am", "start", "-a", "android.intent.action.MAIN",
               "-c", "android.intent.category.LAUNCHER", package_name]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()
