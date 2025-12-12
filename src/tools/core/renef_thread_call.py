from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_thread_call(address: str, args: str = "") -> str:
    """
    Calls a function at the specified memory address.

    Args:
        address: Memory address of the function (e.g., '0x7f8a1c2b0')
        args: Comma-separated list of arguments (e.g., '0x100, 0, 0')

    Returns:
        Function return value
    """
    await proc_module.ensure_started()

    if args:
        lua_code = f'local ret = Thread.call({address}, {args}); print(string.format("Return: 0x%x", ret or 0))'
    else:
        lua_code = f'local ret = Thread.call({address}); print(string.format("Return: 0x%x", ret or 0))'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
