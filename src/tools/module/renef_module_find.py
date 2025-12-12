from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_module_find(lib_name: str) -> str:
    """
    Finds the base address of a loaded library in the target process.

    Args:
        lib_name: Library name (e.g., 'libc.so', 'libflutter.so'). Supports partial matches.

    Returns:
        Base address of the library or nil if not found
    """
    await proc_module.ensure_started()

    lua_code = f'local addr = Module.find("{lib_name}"); if addr then print(string.format("0x%x", addr)) else print("nil") end'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
