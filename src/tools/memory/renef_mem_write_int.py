from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_write_u8(address: str, value: int) -> str:
    """
    Writes an unsigned 8-bit integer to memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        value: Value to write (0-255)

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    lua_code = f'local ok = mem.writeU8({address}, {value}); print(ok and "✓ written" or "✗ failed")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_write_u16(address: str, value: int) -> str:
    """
    Writes an unsigned 16-bit integer to memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        value: Value to write (0-65535)

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    lua_code = f'local ok = mem.writeU16({address}, {value}); print(ok and "✓ written" or "✗ failed")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_write_u32(address: str, value: int) -> str:
    """
    Writes an unsigned 32-bit integer to memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        value: Value to write

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    lua_code = f'local ok = mem.writeU32({address}, {value}); print(ok and "✓ written" or "✗ failed")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_write_u64(address: str, value: int) -> str:
    """
    Writes an unsigned 64-bit integer to memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        value: Value to write

    Returns:
        Success status
    """
    await proc_module.ensure_started()

    lua_code = f'local ok = mem.writeU64({address}, {value}); print(ok and "✓ written" or "✗ failed")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
