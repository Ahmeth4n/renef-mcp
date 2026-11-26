from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_attach(target: str, timeout: float = 30.0) -> str:
    """Attach to a running Android process by PID or package name and inject libagent.so.

    Uses Renef's signal-based injector (no ptrace).

    Args:
        target: Process ID (e.g., "12345") or running package name (e.g., "com.example.app")
        timeout: Injection timeout in seconds (default: 30.0)

    Returns:
        JSON status with attached PID
    """
    try:
        target_str = str(target).strip()
        if not target_str:
            return "ERROR: target PID or package name cannot be empty"

        def _attach():
            client = manager.get_client()
            return client.attach_target(target_str, timeout=timeout)

        session = await manager.call(_attach)
        pkg = None if target_str.isdigit() else target_str
        manager.set_session(session, package=pkg, paused=False)
        return to_json(
            {
                "ok": True,
                "pid": session.pid,
                "target": target_str,
            }
        )
    except Exception as exc:
        return format_error(exc)
