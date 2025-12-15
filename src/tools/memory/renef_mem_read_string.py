from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_read_string(address: str, max_length: int = 1024) -> str:
    """
    Reads a null-terminated string from memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        max_length: Maximum string length to read (default: 1024)

    Returns:
        String value or nil
    """
    await proc_module.ensure_started()

    lua_code = f'local str = Memory.readStr({address}, {max_length}); print(str or "nil")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
