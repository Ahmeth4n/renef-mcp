from src.app import mcp
from src.session import (
    format_error,
    lua_quote,
    manager,
    parse_target_offset_or_symbol,
    to_json,
)


@mcp.tool()
async def renef_hook_native(
    lib_name: str,
    target: str,
    on_enter: str = "",
    on_leave: str = "",
    caller: str = "",
    asynchronous: bool = False,
) -> str:
    """Install a native ARM64 hook on a library function by hex offset or export symbol name.

    Supports all Renef v0.4.0 native hook features:
    - Inline trampoline hooks (default) or PLT/GOT targeted hooks (`caller="libfoo.so"` or `"*"`)
    - Custom Lua `on_enter` (`args[0..7]` = x0-x7) and `on_leave` (`retval` = x0; return value overrides x0)
    - Default argument/return logging when both `on_enter` and `on_leave` are omitted
    - Fire-and-forget async hooks (`asynchronous=True`) for high-frequency observation-only hooks
    - Deferred hooks: if `lib_name` is not loaded yet (e.g., under `renef_spawn(..., pause=True)`),
      the hook is automatically installed the instant the library loads!

    Args:
        lib_name: Library name (e.g., "libc.so", "libnative.so")
        target: Hex offset (e.g., "0x1234") or export symbol name (e.g., "open", "SSL_read")
        on_enter: Optional Lua body for onEnter (`args` table in scope; e.g., 'print(Memory.readStr(args[0]))')
        on_leave: Optional Lua body for onLeave (`retval` in scope; e.g., 'return 0')
        caller: Optional caller library for PLT/GOT hooking (e.g., "libapp.so" or "*")
        asynchronous: If True, runs onEnter off the hot path (observation-only, no onLeave)

    Returns:
        JSON status with hook ID (or deferred flag) and details
    """
    try:
        lib = lib_name.strip()
        if not lib:
            return "ERROR: lib_name cannot be empty"
        parsed_target = parse_target_offset_or_symbol(target)

        if asynchronous and on_leave.strip():
            return "ERROR: asynchronous=True does not support on_leave (observation-only onEnter)."

        enter_src = on_enter.strip()
        leave_src = on_leave.strip()

        # Simple quick-log path via v0.4.0 `hookn` when no custom callbacks or options are given
        if not enter_src and not leave_src and not caller.strip() and not asynchronous:
            def _hookn():
                session = manager.require_session()
                target_arg = f"0x{parsed_target:x}" if isinstance(parsed_target, int) else parsed_target
                out = session.command(f"hookn {lib} {target_arg}").strip()
                if "ERROR:" in out:
                    raise RuntimeError(out)
                return out

            reply = await manager.call(_hookn)
            return to_json(
                {
                    "ok": True,
                    "mode": "hookn",
                    "lib": lib,
                    "target": target,
                    "reply": reply,
                    "hint": "Call `renef_events` to collect logged calls.",
                }
            )

        # Default logger if caller/async set without custom callbacks
        if not enter_src and not leave_src:
            tag = lua_quote(f"{lib}:{target}")
            enter_src = (
                f'print(string.format("[hook %s] tid=%d x0=0x%x x1=0x%x x2=0x%x x3=0x%x", '
                f"{tag}, Thread.id(), args[0] or 0, args[1] or 0, args[2] or 0, args[3] or 0))"
            )
            if not asynchronous:
                leave_src = f'print(string.format("[hook %s] ret=0x%x", {tag}, retval or 0))'

        def _install():
            session = manager.require_session()
            return session.hook(
                lib,
                parsed_target,
                on_enter=enter_src or None,
                on_leave=leave_src or None,
                caller=caller.strip() or None,
                asynchronous=asynchronous,
            )

        hook = await manager.call(_install)
        return to_json(
            {
                "ok": True,
                "hook_id": hook.agent_id,
                "deferred": hook.deferred,
                "description": hook.description,
                "hook_type": "pltgot" if caller.strip() else "trampoline",
                "asynchronous": asynchronous,
                "hint": "Call `renef_events` to collect hook output and `send()` events.",
            }
        )
    except Exception as exc:
        return format_error(exc)
