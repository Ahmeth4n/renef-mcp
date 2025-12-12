from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_memory_dump(address: str, size: int = 64, disassemble: bool = False) -> str:
    """
    Dumps memory at the specified address.

    Args:
        address: Memory address to dump (e.g., '0x7f8a1c2b0')
        size: Number of bytes to dump (default: 64)
        disassemble: If True, shows disassembly (-d flag)

    Returns:
        Memory dump output
    """
    await proc_module.ensure_started()

    if disassemble:
        cmd = f"md {address} {size} -d\n"
    else:
        cmd = f"md {address} {size}\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
