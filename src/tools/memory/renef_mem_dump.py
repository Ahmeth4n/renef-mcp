from src.app import mcp
from src.session import format_error, manager, parse_address


@mcp.tool()
async def renef_mem_dump(
    address: str,
    size: int = 64,
    disassemble: bool = False,
) -> str:
    """Dump or disassemble target memory via server-side `md` (`/proc/<pid>/mem`).

    Args:
        address: Target memory address (e.g., "0x7f8a1c2b0")
        size: Number of bytes to dump (1..4096, default: 64)
        disassemble: If True, disassemble ARM64 instructions (`-d` flag)

    Returns:
        Formatted hex dump or ARM64 disassembly from renef_server
    """
    try:
        addr = parse_address(address)
        if addr == 0:
            return "ERROR: address must be non-zero"
        length = max(1, min(int(size), 4096))
        cmd = f"md 0x{addr:x} {length} -d" if disassemble else f"md 0x{addr:x} {length}"

        def _dump():
            session = manager.require_session()
            return session.command(cmd).strip()

        return await manager.call(_dump)
    except Exception as exc:
        return format_error(exc)
