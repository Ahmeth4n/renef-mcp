from __future__ import annotations

from src.app import mcp
from src.session import (
    format_error,
    manager,
    parse_target_offset_or_symbol,
    to_json,
)


@mcp.tool()
async def renef_interceptor(
    action: str,
    lib_name: str,
    target: str,
    replacement: str = "",
    caller: str = "",
) -> str:
    """Replace or revert a native function using Renef v0.4.0's `Interceptor` API.

    - `action="replace"`: Replaces `(lib_name, target)` so the original never runs (unless invoked
      via `NativeFunction` inside the replacement callback). `replacement` can be an integer
      constant (e.g., `"0"`, `"1"`, `"-1"`), boolean (`"true"`/`"false"`), or a Lua function
      string (`"function(args) return 0 end"`).
    - `action="revert"`: Restores original bytes / GOT entry and removes the hook/replacement.

    Args:
        action: "replace" or "revert"
        lib_name: Library name (e.g., "libnative.so", "libc.so")
        target: Hex offset (e.g., "0x1234") or export symbol name (e.g., "ptrace")
        replacement: (for "replace") Integer/bool constant or Lua function `function(args) ... end`
        caller: Optional caller library name for PLT/GOT replacement (e.g., "libapp.so")

    Returns:
        JSON status
    """
    try:
        act = action.strip().lower()
        if act not in ("replace", "revert"):
            return "ERROR: action must be 'replace' or 'revert'"
        lib = lib_name.strip()
        if not lib:
            return "ERROR: lib_name cannot be empty"
        parsed_target = parse_target_offset_or_symbol(target)

        if act == "replace":
            rep_raw = replacement.strip()
            if not rep_raw:
                return "ERROR: replacement is required for action='replace'"

            rep_val: int | str
            if rep_raw.lower() == "true":
                rep_val = 1
            elif rep_raw.lower() == "false":
                rep_val = 0
            else:
                try:
                    rep_val = int(rep_raw, 0)
                except ValueError:
                    # Allow either full `function(args) ... end` or bare body `return 0`
                    if rep_raw.startswith("function") and rep_raw.endswith("end"):
                        rep_val = rep_raw
                    else:
                        rep_val = f"function(args) {rep_raw} end"

            def _replace():
                session = manager.require_session()
                session.Interceptor.replace(
                    lib, parsed_target, rep_val, caller=caller.strip() or None
                )

            await manager.call(_replace)
            return to_json(
                {
                    "ok": True,
                    "action": "replace",
                    "lib": lib,
                    "target": target,
                    "caller": caller.strip() or None,
                }
            )

        def _revert():
            session = manager.require_session()
            session.Interceptor.revert(lib, parsed_target)

        await manager.call(_revert)
        return to_json({"ok": True, "action": "revert", "lib": lib, "target": target})
    except Exception as exc:
        return format_error(exc)
