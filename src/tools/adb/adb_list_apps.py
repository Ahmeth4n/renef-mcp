import asyncio
from src.app import mcp


@mcp.tool()
async def adb_list_apps(filter: str = "") -> str:
    """
    Lists installed apps on the connected Android device.

    Args:
        filter: Optional filter string to search package names (e.g., 'chrome', 'google')

    Returns:
        List of installed package names
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "pm", "list", "packages",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace")

    # Parse and filter packages
    packages = [line.replace("package:", "").strip() for line in output.splitlines() if line.startswith("package:")]

    if filter:
        packages = [p for p in packages if filter.lower() in p.lower()]

    packages.sort()
    return "\n".join(packages) if packages else "No packages found"
