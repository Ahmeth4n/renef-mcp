import asyncio
import re
from src.app import mcp


@mcp.tool()
async def adb_current_app() -> str:
    """
    Gets the currently focused/active app on the Android device.

    Returns information about the app currently displayed on screen including:
    - Package name
    - Activity name
    - Process ID (PID)
    - User ID (UID)

    Returns:
        JSON string with current app information
    """
    # Get focused window
    proc1 = await asyncio.create_subprocess_exec(
        "adb", "shell", "dumpsys window | grep -A 3 'mCurrentFocus'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout1, _ = await proc1.communicate()
    focus_output = stdout1.decode("utf-8", errors="replace").strip()

    # Get recent activity for PID info
    proc2 = await asyncio.create_subprocess_exec(
        "adb", "shell", "dumpsys activity recents | grep 'Recent #0' -A 10",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout2, _ = await proc2.communicate()
    recents_output = stdout2.decode("utf-8", errors="replace").strip()

    # Parse focused window
    package_name = None
    activity_name = None
    focus_match = re.search(r'mCurrentFocus=Window\{[^\s]+ u\d+ ([^/]+)/([^}]+)\}', focus_output)
    if focus_match:
        package_name = focus_match.group(1)
        activity_name = focus_match.group(2)

    # Parse PID and UID from recents
    pid = None
    uid = None
    pid_match = re.search(r'mRootProcess=ProcessRecord\{[^\s]+ (\d+):([^/]+)/([^}]+)\}', recents_output)
    if pid_match:
        pid = pid_match.group(1)
        uid = pid_match.group(3)

    result = {
        "package": package_name,
        "activity": activity_name,
        "pid": pid,
        "uid": uid,
        "status": "focused" if package_name else "unknown"
    }

    import json
    return json.dumps(result, indent=2)
