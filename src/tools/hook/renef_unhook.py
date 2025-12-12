from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_unhook(hook_id: str = "all") -> str:
    """
    Removes hook(s) by ID or all hooks.

    Args:
        hook_id: Hook ID to remove, or 'all' to remove all hooks (default: 'all')

    Returns:
        Unhook result
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(f"unhook {hook_id}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
