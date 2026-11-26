from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_rpc(expression: str, timeout: float = 30.0) -> str:
    """Evaluate a Lua expression in the target process and return its structured JSON value.

    Uses Renef v0.4.0's `rpc` command: Lua tables become JSON arrays/objects, booleans stay
    true/false, and errors return exact Lua error messages.

    Examples:
        - `OS.getpid()` -> `12345`
        - `{pid = OS.getpid(), tid = Thread.id()}` -> `{"pid": 12345, "tid": 12360}`
        - `Module.find("libc.so")` -> base address integer

    Args:
        expression: Lua expression to evaluate
        timeout: Silence timeout in seconds (default: 30.0)

    Returns:
        JSON object with `ok` and `value`
    """
    try:
        expr = expression.strip()
        if not expr:
            return "ERROR: expression cannot be empty"

        def _rpc():
            session = manager.require_session()
            return session.rpc(expr, timeout=timeout)

        value = await manager.call(_rpc)
        return to_json({"ok": True, "value": value})
    except Exception as exc:
        return format_error(exc)
