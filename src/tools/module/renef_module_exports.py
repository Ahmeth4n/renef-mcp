import fnmatch

from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_module_exports(
    lib_name: str,
    pattern: str = "",
    include_symbols: bool = False,
    limit: int = 200,
) -> str:
    """List or search exported (`.dynsym`) or full (`.symtab`) symbols of a loaded library.

    - Uses Renef v0.4.0's `Module.findExportByName(lib, pattern)` when `pattern` is set and
      `include_symbols=False`. Supports glob wildcards (`*`, `?`) — e.g. `"SSL_*"`, `"*verify*"`,
      or exact names like `"fopen"`.
    - Set `include_symbols=True` to read `.symtab` (`Module.symbols`, empty for stripped binaries).

    Args:
        lib_name: Library name (e.g., "libc.so", "libssl.so", "linker64")
        pattern: Optional glob pattern (`"pthread_*"`, `"*open*"`) or exact symbol name
        include_symbols: If True, inspect `.symtab` (`Module.symbols`) instead of `.dynsym`
        limit: Maximum symbols to return (default: 200)

    Returns:
        JSON object with base address, match counts, and symbol list with offsets
    """
    try:
        lib = lib_name.strip()
        if not lib:
            return "ERROR: lib_name cannot be empty"
        pat = pattern.strip()
        cap = max(1, min(int(limit), 2000))

        def _query():
            session = manager.require_session()
            base = session.Module.find(lib)
            if include_symbols:
                syms = session.Module.symbols(lib)
                if pat:
                    if "*" in pat or "?" in pat:
                        syms = [s for s in syms if fnmatch.fnmatch(s.name, pat)]
                    else:
                        syms = [s for s in syms if pat.lower() in s.name.lower()]
                return base, syms
            if pat:
                syms = session.Module.find_exports(lib, pat)
                return base, syms
            return base, session.Module.exports(lib)

        base, syms = await manager.call(_query)
        shown = syms[:cap]
        return to_json(
            {
                "ok": True,
                "lib": lib,
                "table": "symtab" if include_symbols else "dynsym",
                "base_hex": f"0x{base:x}" if base else None,
                "pattern": pat or None,
                "total_matches": len(syms),
                "returned": len(shown),
                "symbols": [
                    {
                        "name": s.name,
                        "offset": s.offset,
                        "offset_hex": f"0x{s.offset:x}",
                        "address_hex": f"0x{base + s.offset:x}" if base else None,
                    }
                    for s in shown
                ],
            }
        )
    except Exception as exc:
        return format_error(exc)
