from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_search(pattern: str, lib_name: str = "") -> str:
    """
    Searches memory for a string or hex pattern with wildcard support.

    Args:
        pattern: Search pattern - string or hex bytes (e.g., 'secret', 'DEADBEEF', '90??90')
        lib_name: Optional library name to limit search scope

    Returns:
        Table of search results with addresses
    """
    await proc_module.ensure_started()

    if lib_name:
        lua_code = f'local results = mem.search("{pattern}", "{lib_name}"); mem.dump(results)'
    else:
        lua_code = f'local results = mem.search("{pattern}"); mem.dump(results)'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
