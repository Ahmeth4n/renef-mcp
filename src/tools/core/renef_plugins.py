from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_plugins() -> str:
    """
    Lists loaded plugins in the renef server.

    Shows all currently loaded plugins with their names and descriptions.

    Returns:
        List of loaded plugins or "No plugins loaded."
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(b"plugins\n")
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
