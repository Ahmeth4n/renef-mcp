from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_ping(host: str = "", port: int = 0) -> str:
    """Check connectivity to renef_server and report session status.

    Optionally updates the target host/port (defaults to RENEF_HOST/RENEF_PORT or 127.0.0.1:1907).

    Args:
        host: Optional host override (e.g., "127.0.0.1")
        port: Optional TCP port override (e.g., 1907)

    Returns:
        JSON status including pong, framing protocol support, and active target info
    """
    try:
        if host or port:
            manager.configure(host=host or None, port=port or None)

        def _ping():
            client = manager.get_client()
            ok = client.ping()
            return ok, client.framed

        ok, framed = await manager.call(_ping)
        session = manager.get_session()
        queued_events, queued_output = session.pending_counts() if session else (0, 0)
        return to_json(
            {
                "ok": ok,
                "reply": "pong" if ok else "unexpected",
                "host": manager.host,
                "port": manager.port,
                "framed_protocol": framed,
                "active_session": session is not None,
                "target_pid": manager.current_target_pid,
                "target_package": manager.current_target_package,
                "paused": manager.is_paused,
                "queued_events": queued_events,
                "queued_hook_output_lines": queued_output,
            }
        )
    except Exception as exc:
        return format_error(exc)
