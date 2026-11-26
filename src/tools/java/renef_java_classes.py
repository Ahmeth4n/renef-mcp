from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_java_classes(pattern: str = "", limit: int = 200) -> str:
    """Enumerate loaded Java classes from the app's dex files (`Java.enumerateLoadedClasses`).

    Args:
        pattern: Optional case-insensitive substring filter (e.g., "okhttp", "com.example", "Trust")
        limit: Maximum class names to return (default: 200, max: 2000)

    Returns:
        JSON object with total matches and list of class names
    """
    try:
        cap = max(1, min(int(limit), 2000))
        pat = pattern.strip()

        def _enum():
            session = manager.require_session()
            names = session.Java.enumerate_loaded_classes()
            if pat:
                low = pat.lower()
                names = [n for n in names if low in n.lower()]
            return names

        classes = await manager.call(_enum)
        shown = classes[:cap]
        return to_json(
            {
                "ok": True,
                "pattern": pat or None,
                "total_matches": len(classes),
                "returned": len(shown),
                "classes": shown,
            }
        )
    except Exception as exc:
        return format_error(exc)
