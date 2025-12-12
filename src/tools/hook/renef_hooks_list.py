from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_hooks_list() -> str:
    """
    Lists all active hooks.

    Returns:
        List of active hooks with their IDs
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(b"hooks\n")
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
