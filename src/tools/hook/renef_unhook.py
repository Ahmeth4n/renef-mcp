from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_unhook(hook_id: str = "all") -> str:
    """Remove native hook(s), Java hook(s), or all hooks from the target process.

    In Renef v0.4.0, Java hooks can also be removed individually by their `j<id>` ID
    (as shown in `renef_hooks_list`).

    Args:
        hook_id: Hook ID to remove: "all" (default), native ID like "0", or Java ID like "j0"

    Returns:
        JSON status with server reply
    """
    try:
        def _unhook():
            session = manager.require_session()
            return session.unhook_any(hook_id)

        reply = await manager.call(_unhook)
        return to_json({"ok": True, "hook_id": hook_id, "reply": reply})
    except Exception as exc:
        return format_error(exc)
