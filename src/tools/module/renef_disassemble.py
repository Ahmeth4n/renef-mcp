from src.app import mcp
from src.session import format_error, manager, parse_address, to_json


@mcp.tool()
async def renef_disassemble(address: str, count: int = 16) -> str:
    """Disassemble ARM64 instructions at a target address using `Module.disassemble` (Capstone).

    Validates that the entire address range is mapped and readable before disassembling, so
    bad addresses return a clean error instead of crashing the target app.

    Args:
        address: Starting virtual address (e.g., "0x7f8a12340")
        count: Number of ARM64 instructions to decode (1..1024, default: 16)

    Returns:
        JSON object with human-readable `listing` and structured `instructions`
        (including `is_branch`, `is_call`, `is_jump`)
    """
    try:
        addr = parse_address(address)
        cnt = max(1, min(int(count), 1024))

        def _disasm():
            session = manager.require_session()
            return session.Module.disassemble(addr, count=cnt)

        insns = await manager.call(_disasm)
        listing = "\n".join(str(i) for i in insns)
        return to_json(
            {
                "ok": True,
                "address_hex": f"0x{addr:x}",
                "count": len(insns),
                "listing": listing,
                "instructions": [
                    {
                        "address": i.address,
                        "address_hex": f"0x{i.address:x}",
                        "size": i.size,
                        "mnemonic": i.mnemonic,
                        "op_str": i.op_str,
                        "is_branch": i.is_branch,
                        "is_call": i.is_call,
                        "is_jump": i.is_jump,
                    }
                    for i in insns
                ],
            }
        )
    except Exception as exc:
        return format_error(exc)
