from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_module_find(lib_name: str) -> str:
    """Find the base address of a loaded library in the target process (`Module.find`).

    Args:
        lib_name: Library name (e.g., "libc.so", "libflutter.so"). Supports partial matches.

    Returns:
        JSON object with `found`, `base`, and `base_hex`
    """
    try:
        lib = lib_name.strip()
        if not lib:
            return "ERROR: lib_name cannot be empty"

        def _find():
            session = manager.require_session()
            return session.Module.find(lib)

        base = await manager.call(_find)
        return to_json(
            {
                "ok": True,
                "lib": lib,
                "found": bool(base),
                "base": base or None,
                "base_hex": f"0x{base:x}" if base else None,
            }
        )
    except Exception as exc:
        return format_error(exc)
