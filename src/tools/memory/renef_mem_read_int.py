from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_read_u8(address: str) -> str:
    """
    Reads an unsigned 8-bit integer from memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')

    Returns:
        Integer value
    """
    await proc_module.ensure_started()

    lua_code = f'local val = Memory.readU8({address}); print(val and string.format("0x%x (%d)", val, val) or "nil")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_read_u16(address: str) -> str:
    """
    Reads an unsigned 16-bit integer from memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')

    Returns:
        Integer value
    """
    await proc_module.ensure_started()

    lua_code = f'local val = Memory.readU16({address}); print(val and string.format("0x%x (%d)", val, val) or "nil")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_read_u32(address: str) -> str:
    """
    Reads an unsigned 32-bit integer from memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')

    Returns:
        Integer value
    """
    await proc_module.ensure_started()

    lua_code = f'local val = Memory.readU32({address}); print(val and string.format("0x%x (%d)", val, val) or "nil")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_mem_read_u64(address: str) -> str:
    """
    Reads an unsigned 64-bit integer from memory.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')

    Returns:
        Integer value
    """
    await proc_module.ensure_started()

    lua_code = f'local val = Memory.readU64({address}); print(val and string.format("0x%x", val) or "nil")'
    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
