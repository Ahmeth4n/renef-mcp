from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_memory_patch(address: str, hex_bytes: str) -> str:
    """
    Patches memory at the specified address with automatic page protection handling.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        hex_bytes: Hex string of bytes to write (e.g., '90909090', 'C0035FD6')

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    byte_str = ''.join([f'\\x{hex_bytes[i:i+2]}' for i in range(0, len(hex_bytes), 2)])
    lua_code = f'local ok, err = Memory.patch({address}, "{byte_str}"); print(ok and "✓ patched" or "✗ " .. (err or "failed"))'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
