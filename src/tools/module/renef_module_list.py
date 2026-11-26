from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_module_list(filter: str = "", limit: int = 200) -> str:
    """List loaded modules/libraries in the target process with base addresses and sizes.

    Args:
        filter: Optional case-insensitive substring filter on module name or path (e.g., "ssl", "flutter")
        limit: Maximum entries to return (default: 200)

    Returns:
        JSON object with total count and module records
    """
    try:
        cap = max(1, min(int(limit), 2000))

        def _list():
            session = manager.require_session()
            return session.Module.list()

        modules = await manager.call(_list)
        if filter.strip():
            flt = filter.strip().lower()
            modules = [m for m in modules if flt in m.name.lower() or flt in m.path.lower()]

        shown = modules[:cap]
        return to_json(
            {
                "ok": True,
                "total": len(modules),
                "returned": len(shown),
                "modules": [
                    {
                        "name": m.name,
                        "base": m.base,
                        "base_hex": f"0x{m.base:x}",
                        "size": m.size,
                        "size_hex": f"0x{m.size:x}",
                        "path": m.path,
                    }
                    for m in shown
                ],
            }
        )
    except Exception as exc:
        return format_error(exc)
