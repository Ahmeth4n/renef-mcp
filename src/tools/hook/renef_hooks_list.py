from src.app import mcp
from src.session import format_error, manager


@mcp.tool()
async def renef_hooks_list() -> str:
    """List all active native and Java hooks with their IDs (`0`, `j0`, ...) and hit counts.

    Returns:
        Formatted list of active native and Java hooks from the agent
    """
    try:
        def _hooks():
            session = manager.require_session()
            return session.hooks().strip()

        return await manager.call(_hooks)
    except Exception as exc:
        return format_error(exc)
