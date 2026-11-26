from src.app import mcp
from src.session import format_error, manager, parse_address, to_json


@mcp.tool()
async def renef_mem_read(
    address: str,
    size: int = 0,
    format: str = "hex",
) -> str:
    """Safely read memory from the target process (checks /proc/self/maps first to avoid crashes).

    Supported formats:
    - `hex` (default): Raw bytes as hex + printable ASCII preview (`size` defaults to 64, max 1MB)
    - `hexdump`: Formatted classic hexdump (`Memory.hexdump`, `size` defaults to 64)
    - `string`: NUL-terminated UTF-8/C string (`Memory.readStr`, `size` defaults to 256)
    - `u8`, `u16`, `u32`, `u64`, `pointer`: Little-endian unsigned integer

    Args:
        address: Target memory address (e.g., "0x7f8a1c2b0")
        size: Number of bytes for hex/hexdump (default 64) or max length for string (default 256)
        format: Output format - "hex", "hexdump", "string", "u8", "u16", "u32", "u64", "pointer"

    Returns:
        JSON object with the read value (or formatted hexdump)
    """
    try:
        addr = parse_address(address)
        fmt = format.strip().lower()
        valid = ("hex", "hexdump", "string", "u8", "u16", "u32", "u64", "pointer")
        if fmt not in valid:
            return f"ERROR: format must be one of {', '.join(valid)}"

        def _read():
            session = manager.require_session()
            mem = session.Memory
            if fmt == "u8":
                val = mem.read_u8(addr)
                return {"address": f"0x{addr:x}", "type": "u8", "value": val, "hex": f"0x{val:02x}"}
            if fmt == "u16":
                val = mem.read_u16(addr)
                return {"address": f"0x{addr:x}", "type": "u16", "value": val, "hex": f"0x{val:04x}"}
            if fmt == "u32":
                val = mem.read_u32(addr)
                return {"address": f"0x{addr:x}", "type": "u32", "value": val, "hex": f"0x{val:08x}"}
            if fmt in ("u64", "pointer"):
                val = mem.read_u64(addr)
                return {"address": f"0x{addr:x}", "type": fmt, "value": val, "hex": f"0x{val:016x}"}
            if fmt == "string":
                max_len = max(1, min(int(size) if size > 0 else 256, 65536))
                text = mem.read_string(addr, max_len=max_len)
                return {"address": f"0x{addr:x}", "type": "string", "value": text}
            if fmt == "hexdump":
                length = max(1, min(int(size) if size > 0 else 64, 65536))
                dump = mem.hexdump(addr, length=length).rstrip("\x00")
                return {"address": f"0x{addr:x}", "type": "hexdump", "size": length, "hexdump": dump}
            # hex
            length = max(1, min(int(size) if size > 0 else 64, 1024 * 1024))
            raw = mem.read(addr, length)
            if raw is None:
                return {"address": f"0x{addr:x}", "type": "hex", "bytes": None}
            ascii_preview = "".join(chr(b) if 32 <= b < 127 else "." for b in raw[:256])
            return {
                "address": f"0x{addr:x}",
                "size": len(raw),
                "hex": raw.hex(),
                "hex_spaced": " ".join(f"{b:02x}" for b in raw),
                "ascii": ascii_preview,
            }

        result = await manager.call(_read)
        return to_json({"ok": True, **result})
    except Exception as exc:
        return format_error(exc)
