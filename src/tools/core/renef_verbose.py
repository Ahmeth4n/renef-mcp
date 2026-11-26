from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_verbose(enabled: bool) -> str:
    """Toggle verbose debug logging inside the injected agent (`verbose on` / `verbose off`).

    Args:
        enabled: True to enable verbose agent logs, False to disable

    Returns:
        JSON status with server reply
    """
    try:
        mode = "on" if enabled else "off"

        def _verbose():
            session = manager.require_session()
            return session.command(f"verbose {mode}").strip()

        reply = await manager.call(_verbose)
        return to_json({"ok": True, "verbose": enabled, "reply": reply})
    except Exception as exc:
        return format_error(exc)
