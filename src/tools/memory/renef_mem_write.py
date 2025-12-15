from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_write(address: str, hex_bytes: str) -> str:
    """
    Writes raw bytes to memory at the specified address.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        hex_bytes: Hex string of bytes to write (e.g., '90909090', 'C0035FD6')

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    lua_code = f'local ok = Memory.write({address}, "\\x{hex_bytes}"); print(ok and "✓ written" or "✗ failed")'
    # Need to properly escape the hex bytes
    byte_str = ''.join([f'\\x{hex_bytes[i:i+2]}' for i in range(0, len(hex_bytes), 2)])
    lua_code = f'local ok = Memory.write({address}, "{byte_str}"); print(ok and "✓ written" or "✗ failed")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
