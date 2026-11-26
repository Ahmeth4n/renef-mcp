from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_exec(lua_code: str, timeout: float = 30.0) -> str:
    """Execute single-line or multi-line Lua 5.4 code in the target process.

    Uses Renef v0.4.0's framed protocol and safe quoting (no 64 KB limit, no temp files,
    safe with newlines, quotes, `//`, and `~`). Returns printed output and exact Lua
    compile/runtime error messages.

    IMPORTANT: Use Renef Lua API (`hook`, `Interceptor`, `NativeFunction`, `Memory`,
    `Module`, `Process`, `Thread`, `Java`, `Jni`, `Syscall`, `OS`, `File`, `KCov`, `send`),
    NOT Frida JS syntax. See `renef://api-reference`.

    Args:
        lua_code: Lua code to execute in the target process
        timeout: Silence timeout in seconds (default: 30.0)

    Returns:
        JSON object with `ok`, `output`, `error`, and any queued event hint
    """
    try:
        if not lua_code or not lua_code.strip():
            return "ERROR: lua_code cannot be empty"

        def _exec():
            session = manager.require_session()
            result = session.eval(lua_code, timeout=timeout)
            ev_count, out_count = session.pending_counts()
            return result, ev_count, out_count

        result, ev_count, out_count = await manager.call(_exec)
        if result.ok:
            manager.mark_exec_completed()
        payload = {
            "ok": result.ok,
            "output": result.output or "",
            "error": result.error,
        }
        if ev_count or out_count:
            payload["queued_events"] = ev_count
            payload["queued_hook_output_lines"] = out_count
            payload["hint"] = "Call `renef_events` to retrieve queued hook/send() events."
        return to_json(payload)
    except Exception as exc:
        return format_error(exc)
