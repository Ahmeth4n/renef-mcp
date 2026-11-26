import shlex
from pathlib import Path

from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_load_script(script_paths: str, timeout: float = 30.0) -> str:
    """Load and execute one or more local Lua script files in the target process.

    Reads the file(s) on the host and sends them over Renef v0.4.0's framed protocol
    (supports scripts of any size with full Lua error reporting).

    Args:
        script_paths: Path to a Lua file, or space-separated paths to multiple files
                      (e.g., "hook.lua" or "taint_filter.lua root_emulator_bypass.lua")
        timeout: Execution timeout per script in seconds (default: 30.0)

    Returns:
        JSON summary with per-script execution results
    """
    try:
        raw = script_paths.strip()
        if not raw:
            return "ERROR: script_paths cannot be empty"

        # If the whole string is a valid path (e.g. contains spaces), treat as single path
        if Path(raw).is_file():
            paths = [raw]
        else:
            paths = shlex.split(raw)

        def _load_all():
            session = manager.require_session()
            results = []
            for p in paths:
                res = session.load_script(p, timeout=timeout)
                results.append(
                    {
                        "path": p,
                        "ok": res.ok,
                        "output": res.output or "",
                        "error": res.error,
                    }
                )
            return results

        results = await manager.call(_load_all)
        all_ok = all(r["ok"] for r in results)
        if any(r["ok"] for r in results):
            manager.mark_exec_completed()
        return to_json({"ok": all_ok, "scripts": results})
    except Exception as exc:
        return format_error(exc)
