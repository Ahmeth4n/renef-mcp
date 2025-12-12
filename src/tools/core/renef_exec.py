from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_exec(lua_code: str) -> str:
    """
    Executes Lua code in the target process.

    Args:
        lua_code: Lua code to execute (e.g., 'Module.list()', 'print("hello")')

    Returns:
        Execution result
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
