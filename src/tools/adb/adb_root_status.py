import asyncio
from src.app import mcp


@mcp.tool()
async def adb_root_status() -> str:
    """
    Checks if the Android device is rooted and provides detailed root status.

    Returns:
        Root status with details about available root methods
    """
    results = []

    # Check adb root access
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "whoami",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    whoami = stdout.decode("utf-8", errors="replace").strip()
    results.append(f"ADB shell user: {whoami}")

    # Check if su binary exists
    su_paths = ["/system/bin/su", "/system/xbin/su", "/sbin/su", "/data/local/tmp/su"]
    su_found = []
    for path in su_paths:
        proc = await asyncio.create_subprocess_exec(
            "adb", "shell", f"test -f {path} && echo exists",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        if "exists" in stdout.decode():
            su_found.append(path)

    if su_found:
        results.append(f"su binary: ✓ found at {', '.join(su_found)}")
    else:
        results.append("su binary: ✗ not found")

    # Check if su works
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "su -c id",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    su_output = stdout.decode("utf-8", errors="replace").strip()
    if "uid=0" in su_output:
        results.append("su access: ✓ working (uid=0)")
    else:
        results.append(f"su access: ✗ not working")

    # Check Magisk
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "magisk -v",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    magisk_output = stdout.decode("utf-8", errors="replace").strip()
    if magisk_output and "not found" not in magisk_output.lower():
        results.append(f"Magisk: ✓ {magisk_output}")
    else:
        results.append("Magisk: ✗ not found")

    # Overall status
    is_rooted = whoami == "root" or "uid=0" in su_output or su_found
    results.insert(0, f"Root status: {'✓ ROOTED' if is_rooted else '✗ NOT ROOTED'}\n")

    return "\n".join(results)
