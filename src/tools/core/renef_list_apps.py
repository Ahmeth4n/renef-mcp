from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_list_apps(filter: str = "") -> str:
    """List installed applications on the Android device via renef_server (no injection needed).

    Args:
        filter: Optional substring filter for package names (e.g., "chrome", "example")

    Returns:
        JSON object with count and sorted package names
    """
    try:
        def _list():
            client = manager.get_client()
            return client.list_apps(filter or None)

        apps = await manager.call(_list)
        return to_json({"count": len(apps), "packages": apps})
    except Exception as exc:
        return format_error(exc)
