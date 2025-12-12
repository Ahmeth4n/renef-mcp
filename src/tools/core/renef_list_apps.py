from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_list_apps(filter: str = "") -> str:
    """
    Lists installed applications on the Android device via renef.

    Args:
        filter: Optional filter string (e.g., 'chrome', 'google')

    Returns:
        List of installed apps
    """
    await proc_module.ensure_started()

    if filter:
        cmd = f"la~{filter}\n"
    else:
        cmd = "la\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
