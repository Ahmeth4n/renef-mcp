from src.app import mcp
from src.session import format_error, run_adb


@mcp.tool()
async def adb_devices() -> str:
    """List connected Android devices (`adb devices -l`).

    Returns:
        Connected ADB devices output
    """
    try:
        _, out = await run_adb("devices", "-l", timeout=10.0)
        return out or "No ADB devices found."
    except Exception as exc:
        return format_error(exc)
