from src.app import mcp
from src.session import format_error, manager, to_json, u64


@mcp.tool()
async def renef_kcov(
    action: str,
    buf_size: int = 0,
    max_entries: int = 256,
) -> str:
    """Kernel coverage collection via Linux KCOV (`KCov.*` API; requires kernel `CONFIG_KCOV=y`).

    Manages a session-wide `_kcov` handle in the target's Lua VM.

    Actions:
    - `start`: Open `/sys/kernel/debug/kcov` with optional `buf_size` (default 256K entries) and enable recording
    - `enable`: Re-enable recording on the open `_kcov` handle
    - `disable`: Pause recording (buffer preserved for `collect`/`edges`)
    - `count`: Return number of recorded kernel PCs without copying
    - `collect`: Collect recorded kernel PC addresses (hex list, capped at `max_entries`)
    - `edges`: Compute AFL-style unique kernel edge hashes and total edge count
    - `reset`: Clear the KCOV buffer for a fresh measurement
    - `stop`: Disable and close the KCOV handle

    Args:
        action: "start", "enable", "disable", "count", "collect", "edges", "reset", or "stop"
        buf_size: Number of PC entries for `action="start"` (0 = default 256K entries / 2MB)
        max_entries: Maximum PCs/edges returned in JSON (default: 256, max: 8192)

    Returns:
        JSON object with coverage state or collected kernel PCs/edges
    """
    try:
        act = action.strip().lower()
        valid = ("start", "enable", "disable", "count", "collect", "edges", "reset", "stop")
        if act not in valid:
            return f"ERROR: action must be one of {', '.join(valid)}"

        cap = max(1, min(int(max_entries), 8192))

        if act == "start":
            def _start():
                session = manager.require_session()
                return session.KCov.start(int(buf_size))

            res = await manager.call(_start)
            if not res.ok:
                return f"ERROR [kcov]: {res.error or res.output}"
            return to_json({"ok": True, "action": "start", "output": res.output or ""})

        if act == "stop":
            def _stop():
                session = manager.require_session()
                return session.KCov.stop()

            res = await manager.call(_stop)
            if not res.ok:
                return f"ERROR [kcov]: {res.error or res.output}"
            return to_json({"ok": True, "action": "stop"})

        if act == "enable":
            def _enable():
                session = manager.require_session()
                return session.eval('if not _kcov then error("KCov not opened; call start first", 0) end; _kcov:enable()')

            res = await manager.call(_enable)
            if not res.ok:
                return f"ERROR [kcov]: {res.error or res.output}"
            return to_json({"ok": True, "action": "enable"})

        if act == "disable":
            def _disable():
                session = manager.require_session()
                return session.eval('if not _kcov then error("KCov not opened; call start first", 0) end; _kcov:disable()')

            res = await manager.call(_disable)
            if not res.ok:
                return f"ERROR [kcov]: {res.error or res.output}"
            return to_json({"ok": True, "action": "disable"})

        if act == "reset":
            def _reset():
                session = manager.require_session()
                return session.KCov.reset()

            res = await manager.call(_reset)
            if not res.ok:
                return f"ERROR [kcov]: {res.error or res.output}"
            return to_json({"ok": True, "action": "reset"})

        if act == "count":
            def _count():
                session = manager.require_session()
                return session.KCov.count()

            cnt = await manager.call(_count)
            return to_json({"ok": cnt is not None and cnt >= 0, "action": "count", "count": cnt})

        if act == "collect":
            def _collect():
                session = manager.require_session()
                rows = session.rpc(
                    f"(function() if not _kcov then return nil end return _kcov:collect({cap}) end)()"
                )
                return [u64(pc) for pc in rows] if isinstance(rows, list) else None

            pcs = await manager.call(_collect)
            if pcs is None:
                return "ERROR [kcov]: KCov not opened; call action='start' first"
            return to_json(
                {
                    "ok": True,
                    "action": "collect",
                    "count": len(pcs),
                    "pcs": [f"0x{pc:x}" for pc in pcs],
                }
            )

        # edges
        def _edges():
            session = manager.require_session()
            return session.rpc(
                "(function() if not _kcov then return nil end return _kcov:edges() end)()"
            )

        edges = await manager.call(_edges)
        if edges is None:
            return "ERROR [kcov]: KCov not opened; call action='start' first"
        items = list(edges.items()) if isinstance(edges, dict) else []
        return to_json(
            {
                "ok": True,
                "action": "edges",
                "unique_edges": len(items),
                "sample": dict(items[:cap]),
            }
        )
    except Exception as exc:
        return format_error(exc)
