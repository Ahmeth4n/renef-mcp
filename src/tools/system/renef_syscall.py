from typing import List, Optional

from src.app import mcp
from src.session import format_error, lua_quote, manager, to_json


@mcp.tool()
async def renef_syscall(
    action: str,
    syscalls: Optional[List[str]] = None,
    category: str = "",
    caller: str = "",
) -> str:
    """Trace Linux/Android syscalls in the target process (`Syscall.*` API).

    Actions:
    - `trace`: Trace specific syscalls (`syscalls=["openat", "read", "connect"]`, optional `caller="libapp.so"`)
      OR trace an entire `category` (`"file"`, `"network"`, `"memory"`, `"process"`, `"ipc"`)
    - `trace_all`: Trace all supported syscalls (`Syscall.traceAll()`)
    - `untrace`: Stop tracing specific syscalls (`syscalls=[...]`)
    - `stop`: Stop all active syscall tracing (`Syscall.stop()`)
    - `list`: List available traceable syscalls (optional `category` filter)
    - `active`: Show currently active syscall traces

    Note: Syscall trace lines are delivered on the separate event channel — call `renef_events`
    to read captured syscall traces!

    Args:
        action: "trace", "trace_all", "untrace", "stop", "list", or "active"
        syscalls: List of syscall names (for "trace" / "untrace")
        category: Syscall category ("file", "network", "memory", "process", "ipc")
        caller: Optional caller library filter when tracing named syscalls (e.g., "libtarget.so")

    Returns:
        JSON status or list of syscalls/active traces
    """
    try:
        act = action.strip().lower()
        valid = ("trace", "trace_all", "untrace", "stop", "list", "active")
        if act not in valid:
            return f"ERROR: action must be one of {', '.join(valid)}"

        names = [s.strip() for s in (syscalls or []) if s and s.strip()]
        cat = category.strip()
        caller_lib = caller.strip()

        if act == "list":
            expr = f"Syscall.list({lua_quote(cat)})" if cat else "Syscall.list()"

            def _list():
                session = manager.require_session()
                return session.rpc(expr) or []

            items = await manager.call(_list)
            return to_json({"ok": True, "category": cat or "all", "count": len(items), "syscalls": items})

        if act == "active":
            def _active():
                session = manager.require_session()
                return session.Syscall.active() or []

            active = await manager.call(_active)
            return to_json({"ok": True, "count": len(active), "active_traces": active})

        if act == "stop":
            def _stop():
                session = manager.require_session()
                return session.Syscall.stop()

            res = await manager.call(_stop)
            if not res.ok:
                return f"ERROR [lua]: {res.error or res.output}"
            return to_json({"ok": True, "action": "stop", "output": res.output or "Syscall tracing stopped"})

        if act == "trace_all":
            def _all():
                session = manager.require_session()
                return session.Syscall.trace_all()

            res = await manager.call(_all)
            if not res.ok:
                return f"ERROR [lua]: {res.error or res.output}"
            return to_json(
                {
                    "ok": True,
                    "action": "trace_all",
                    "output": res.output or "",
                    "hint": "Call `renef_events` to read syscall trace lines.",
                }
            )

        if act == "untrace":
            if not names:
                return "ERROR: syscalls list is required for action='untrace'"

            def _untrace():
                session = manager.require_session()
                return session.Syscall.untrace(*names)

            res = await manager.call(_untrace)
            if not res.ok:
                return f"ERROR [lua]: {res.error or res.output}"
            return to_json({"ok": True, "action": "untrace", "syscalls": names, "output": res.output or ""})

        # action == "trace"
        if cat and not names:
            def _trace_cat():
                session = manager.require_session()
                return session.Syscall.trace_category(cat)

            res = await manager.call(_trace_cat)
            if not res.ok:
                return f"ERROR [lua]: {res.error or res.output}"
            return to_json(
                {
                    "ok": True,
                    "action": "trace",
                    "category": cat,
                    "output": res.output or "",
                    "hint": "Call `renef_events` to read syscall trace lines.",
                }
            )

        if not names:
            return "ERROR: provide `syscalls` list or `category` for action='trace'"

        args_lua = ", ".join(lua_quote(n) for n in names)
        if caller_lib:
            lua_code = f"Syscall.trace({args_lua}, {{ caller = {lua_quote(caller_lib)} }})"
        else:
            lua_code = f"Syscall.trace({args_lua})"

        def _trace():
            session = manager.require_session()
            return session.eval(lua_code)

        res = await manager.call(_trace)
        if not res.ok:
            return f"ERROR [lua]: {res.error or res.output}"
        return to_json(
            {
                "ok": True,
                "action": "trace",
                "syscalls": names,
                "caller": caller_lib or None,
                "output": res.output or "",
                "hint": "Call `renef_events` to read syscall trace lines.",
            }
        )
    except Exception as exc:
        return format_error(exc)
