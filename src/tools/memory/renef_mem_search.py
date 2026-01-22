from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_search(pattern: str, lib_name: str = "") -> str:
    """
    Searches memory for a string or hex pattern with wildcard support.

    Pattern formats:
    - Plain string: 'hello' or 'secret'
    - Hex bytes: 'DEADBEEF' or 'DE AD BE EF' (spaces optional)
    - Wildcards: 'DE ?? AD BE' where ?? matches any byte
    - Mixed: '48 65 6C 6C 6F' (hex for 'Hello')

    Args:
        pattern: Search pattern - string, hex bytes, or hex with ?? wildcards
        lib_name: Optional library name to limit search scope (e.g., 'libc.so')

    Returns:
        Formatted search results showing library, offset, address, hex dump, and ASCII
    """
    await proc_module.ensure_started()

    if lib_name:
        lua_code = f'local results = Memory.search("{pattern}", "{lib_name}"); Memory.dump(results)'
    else:
        lua_code = f'local results = Memory.search("{pattern}"); Memory.dump(results)'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
