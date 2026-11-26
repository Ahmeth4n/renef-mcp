from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_spawn(
    package_name: str,
    pause: bool = False,
    hold: bool = True,
    timeout: float = 30.0,
) -> str:
    """Spawn an Android app and inject the Renef v0.4.0 agent (libagent.so).

    Default injection (`pause=False`) is signal-based (NO ptrace, immune to TracerPid checks).
    With `pause=True`, uses the ptrace spawn gate to freeze the main thread before app code runs
    so deferred hooks on not-yet-loaded libraries catch the very first call.

    Anti-debug note: `pause=True` sets TracerPid != 0 while paused. Prefer `pause=False` against
    targets suspected of anti-debug/ptrace checks unless early-hook timing is specifically needed.

    Args:
        package_name: Android package name (e.g., "com.example.app")
        pause: Freeze the app at startup via ptrace spawn gate (default: False)
        hold: When `pause=True`, keep the app frozen across multiple exec/hook calls until
              `renef_resume()` is explicitly called (default: True)
        timeout: Spawn & injection timeout in seconds (default: 30.0)

    Returns:
        JSON status with spawned PID and next-step guidance
    """
    try:
        pkg = package_name.strip()
        if not pkg:
            return "ERROR: package_name cannot be empty"

        def _spawn():
            client = manager.get_client()
            return client.spawn_app(pkg, pause=pause, hold=hold, timeout=timeout)

        session = await manager.call(_spawn)
        manager.set_session(session, package=pkg, paused=pause, hold=hold)

        res = {
            "ok": True,
            "pid": session.pid,
            "package": pkg,
            "paused": pause,
            "hold": pause and hold,
        }
        if pause:
            res["note"] = (
                "Target is paused at spawn gate. Install hooks/scripts now, then call "
                "`renef_resume()` to let the app run."
                if hold
                else "Target is paused and will auto-resume on the first `renef_exec` / `renef_load_script`."
            )
        return to_json(res)
    except Exception as exc:
        return format_error(exc)
