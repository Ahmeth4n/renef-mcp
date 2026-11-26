from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_mem_search(
    pattern: str,
    lib_name: str = "",
    limit: int = 100,
) -> str:
    """Search target process memory for a string, hex byte sequence, or wildcard hex pattern.

    Pattern formats:
    - Plain string: `"secret"`, `"https://api"`
    - Hex bytes: `"DEADBEEF"` or `"FD 7B ?? A9"` (`??` matches any byte)

    Args:
        pattern: String or hex/wildcard search pattern
        lib_name: Optional library name to scope the search (e.g., "libnative.so")
        limit: Maximum matches to return (default: 100)

    Returns:
        JSON object with total hit count and structured match records
    """
    try:
        pat = pattern.strip()
        if not pat:
            return "ERROR: pattern cannot be empty"
        cap = max(1, min(int(limit), 1000))

        def _search():
            session = manager.require_session()
            return session.Memory.search(pat, lib=lib_name.strip() or None)

        hits = await manager.call(_search)
        shown = hits[:cap]
        return to_json(
            {
                "ok": True,
                "pattern": pat,
                "lib_filter": lib_name.strip() or None,
                "total_matches": len(hits),
                "returned": len(shown),
                "matches": [
                    {
                        "addr": h.addr,
                        "addr_hex": f"0x{h.addr:x}",
                        "offset": h.offset,
                        "offset_hex": f"0x{h.offset:x}",
                        "library": h.library,
                        "hex": h.hex,
                        "ascii": h.ascii,
                    }
                    for h in shown
                ],
            }
        )
    except Exception as exc:
        return format_error(exc)
