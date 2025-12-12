from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_hook_native(lib_name: str, offset: str) -> str:
    """
    Installs a native hook at the specified offset in a library.

    Args:
        lib_name: Name of the library (e.g., 'libnative.so')
        offset: Hex offset in the library (e.g., '0x1234' or '1234')

    Returns:
        Hook installation result
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(f"hookn {lib_name} {offset}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
