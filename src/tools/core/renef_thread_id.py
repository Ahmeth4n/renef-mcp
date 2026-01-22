from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_thread_id() -> str:
    """
    Gets the current thread ID (TID) in the target process.

    Returns:
        Thread ID as integer
    """
    await proc_module.ensure_started()

    lua_code = 'print(Thread.id())'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
