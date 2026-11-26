from src.app import mcp
from src.session import format_error, manager, parse_address, parse_hex_bytes, to_json


@mcp.tool()
async def renef_mem_write(
    address: str,
    value: str,
    type: str = "hex",
    patch: bool = False,
) -> str:
    """Write bytes or integers to target process memory (with optional code-page patching).

    - When `patch=True` (or writing to read-only/executable code pages), uses `Memory.patch`
      which automatically handles `mprotect` and instruction cache flushing.
    - Supports `type`: `"hex"` (e.g. `"C0035FD6"` = ARM64 `RET`), `"u8"`, `"u16"`, `"u32"`, `"u64"`.

    Args:
        address: Target memory address (e.g., "0x7f8a1c2b0")
        value: Hex bytes string (for type="hex") or integer string (decimal or "0x..." hex)
        type: Data type - "hex" (default), "u8", "u16", "u32", "u64"
        patch: Force `Memory.patch` (auto mprotect for RX/RO code pages)

    Returns:
        JSON status confirming bytes written
    """
    try:
        addr = parse_address(address)
        if addr == 0:
            return "ERROR: address must be non-zero"
        dtype = type.strip().lower()
        int_sizes = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}

        if dtype == "hex":
            data = parse_hex_bytes(value)
        elif dtype in int_sizes:
            size = int_sizes[dtype]
            num = int(str(value).strip(), 0)
            mask = (1 << (8 * size)) - 1
            data = (num & mask).to_bytes(size, "little")
        else:
            return "ERROR: type must be 'hex', 'u8', 'u16', 'u32', or 'u64'"

        def _write():
            session = manager.require_session()
            if patch:
                session.Memory.patch(addr, data)
                return len(data), "patch"
            written = session.Memory.write(addr, data)
            return written, "write"

        written, method = await manager.call(_write)
        return to_json(
            {
                "ok": True,
                "address": f"0x{addr:x}",
                "method": method,
                "bytes_written": written,
                "hex": data.hex(),
            }
        )
    except Exception as exc:
        return format_error(exc)
