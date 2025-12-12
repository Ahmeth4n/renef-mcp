from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_module_list() -> str:
    """
    Lists all loaded .so libraries in the target process with their addresses.

    Returns:
        List of loaded libraries with base addresses
    """
    await proc_module.ensure_started()

    lua_code = 'print(Module.list())'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
