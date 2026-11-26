from src.app import mcp
from src.session import format_error, manager, run_adb, to_json


@mcp.tool()
async def renef_events(wait_ms: int = 0, include_logcat: bool = False) -> str:
    """Collect hook output, syscall trace lines, and structured `send({...})` JSON events.

    In Renef v0.4.0, hook callbacks and syscall tracers emit to a dedicated event channel
    separate from normal command replies. Call this tool to retrieve buffered events or wait
    up to `wait_ms` milliseconds for new ones.

    Args:
        wait_ms: Milliseconds to wait for incoming events (0 = immediate drain, max 30000)
        include_logcat: Also fetch recent `RENEF_LUA` lines from Android logcat as fallback

    Returns:
        JSON object with `events` (structured `send()` payloads), `output` (printed hook/trace
        lines), and optionally `logcat`
    """
    try:
        clamped_ms = max(0, min(int(wait_ms), 30000))

        def _poll():
            session = manager.require_session()
            return session.poll_all(wait_ms=clamped_ms)

        structured, output = await manager.call(_poll)
        result = {
            "event_count": len(structured),
            "output_line_count": len(output),
            "events": structured,
            "output": output,
        }

        if include_logcat:
            rc, log_out = await run_adb("logcat", "-d", "-t", "200", "-s", "RENEF_LUA:I", timeout=10.0)
            log_lines = []
            if rc == 0 and log_out:
                for line in log_out.splitlines():
                    if "[SCRIPT]" in line:
                        log_lines.append(line.split("[SCRIPT]", 1)[1].strip())
                    elif "[SEND]" in line:
                        log_lines.append("[event] " + line.split("[SEND]", 1)[1].strip())
            result["logcat"] = log_lines

        return to_json(result)
    except Exception as exc:
        return format_error(exc)
