from src.app import mcp
from src.session import format_error, manager, parse_address, to_json


@mcp.tool()
async def renef_mem_manage(
    action: str,
    address: str = "",
    size: int = 0,
    text: str = "",
    prot: str = "rw-",
) -> str:
    """Allocate, free, or change page permissions in target process memory (Renef v0.4.0 API).

    Actions:
    - `alloc`: Allocate `size` bytes with permissions `prot` (e.g., `"rw-"`, `"rwx"`, `"r-x"`) -> `Memory.alloc`
    - `alloc_str`: Allocate a NUL-terminated copy of `text` in target memory -> `Memory.allocStr`
    - `free`: Free memory allocated at `address` (optional `size`) -> `Memory.free`
    - `protect`: Change memory protection of `[address, address+size)` to `prot` -> `Memory.protect`

    Args:
        action: "alloc", "alloc_str", "free", or "protect"
        address: Memory address (required for "free" and "protect")
        size: Byte size (required for "alloc" and "protect"; optional for "free")
        text: String content (required for "alloc_str")
        prot: Permission string like "rw-", "r-x", "rwx" (default: "rw-")

    Returns:
        JSON object with result address or confirmation
    """
    try:
        act = action.strip().lower()
        if act not in ("alloc", "alloc_str", "free", "protect"):
            return "ERROR: action must be 'alloc', 'alloc_str', 'free', or 'protect'"

        if act == "alloc":
            if size <= 0:
                return "ERROR: size must be > 0 for action='alloc'"

            def _alloc():
                session = manager.require_session()
                return session.Memory.alloc(int(size), prot=prot)

            ptr = await manager.call(_alloc)
            return to_json(
                {
                    "ok": True,
                    "action": "alloc",
                    "address": ptr,
                    "address_hex": f"0x{ptr:x}",
                    "size": int(size),
                    "prot": prot,
                }
            )

        if act == "alloc_str":
            def _alloc_str():
                session = manager.require_session()
                return session.Memory.alloc_str(text)

            ptr = await manager.call(_alloc_str)
            return to_json(
                {
                    "ok": True,
                    "action": "alloc_str",
                    "address": ptr,
                    "address_hex": f"0x{ptr:x}",
                    "length": len(text.encode("utf-8")),
                }
            )

        addr = parse_address(address)
        if act == "free":
            def _free():
                session = manager.require_session()
                session.Memory.free(addr, int(size) if size > 0 else None)

            await manager.call(_free)
            return to_json({"ok": True, "action": "free", "address_hex": f"0x{addr:x}"})

        # protect
        if size <= 0:
            return "ERROR: size must be > 0 for action='protect'"

        def _protect():
            session = manager.require_session()
            session.Memory.protect(addr, int(size), prot)

        await manager.call(_protect)
        return to_json(
            {
                "ok": True,
                "action": "protect",
                "address_hex": f"0x{addr:x}",
                "size": int(size),
                "prot": prot,
            }
        )
    except Exception as exc:
        return format_error(exc)
