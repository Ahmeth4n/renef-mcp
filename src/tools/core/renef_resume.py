from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_resume() -> str:
    """Resume a target process that was spawned with `renef_spawn(..., pause=True)`.

    Detaches the ptrace spawn gate so app code runs and any deferred hooks install
    as their target libraries load.

    Returns:
        JSON status with server response
    """
    try:
        def _resume():
            session = manager.require_session()
            return session.resume().strip()

        reply = await manager.call(_resume)
        manager.is_paused = False
        return to_json({"ok": True, "reply": reply, "paused": False})
    except Exception as exc:
        return format_error(exc)
