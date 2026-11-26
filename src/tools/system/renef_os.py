from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_os(
    action: str,
    path: str = "",
    pid: int = 0,
    tid: int = 0,
    signal: int = 0,
) -> str:
    """OS-level helpers executed inside the target process (`OS.*` API).

    Actions:
    - `getpid`: Get the target process's PID (`OS.getpid()`)
    - `listdir`: List non-dot entries of a directory on device (`OS.listdir(path)`)
    - `kill`: Send a POSIX signal to a PID (`OS.kill(pid, signal)`)
    - `tgkill`: Send a POSIX signal to a specific thread (`OS.tgkill(pid, tid, signal)`)

    Args:
        action: "getpid", "listdir", "kill", or "tgkill"
        path: Directory path on device (required for "listdir", e.g., "/proc/self/task")
        pid: Target process/thread-group ID (required for "kill" and "tgkill")
        tid: Target thread ID (required for "tgkill")
        signal: POSIX signal number (required for "kill" and "tgkill", e.g., 9, 15, 19)

    Returns:
        JSON object with operation result
    """
    try:
        act = action.strip().lower()
        if act not in ("getpid", "listdir", "kill", "tgkill"):
            return "ERROR: action must be 'getpid', 'listdir', 'kill', or 'tgkill'"

        if act == "getpid":
            def _pid():
                session = manager.require_session()
                return session.OS.getpid()

            val = await manager.call(_pid)
            return to_json({"ok": True, "action": "getpid", "pid": val})

        if act == "listdir":
            p = path.strip()
            if not p:
                return "ERROR: path is required for action='listdir'"

            def _ls():
                session = manager.require_session()
                return session.OS.listdir(p)

            entries = await manager.call(_ls)
            return to_json(
                {
                    "ok": entries is not None,
                    "action": "listdir",
                    "path": p,
                    "count": len(entries) if entries is not None else 0,
                    "entries": entries,
                }
            )

        if act == "kill":
            if pid <= 0:
                return "ERROR: pid must be > 0 for action='kill'"

            def _kill():
                session = manager.require_session()
                return session.OS.kill(int(pid), int(signal))

            ret = await manager.call(_kill)
            return to_json({"ok": ret == 0, "action": "kill", "pid": int(pid), "signal": int(signal), "ret": ret})

        # tgkill
        if pid <= 0 or tid <= 0:
            return "ERROR: pid and tid must be > 0 for action='tgkill'"

        def _tgkill():
            session = manager.require_session()
            return session.OS.tgkill(int(pid), int(tid), int(signal))

        ret = await manager.call(_tgkill)
        return to_json(
            {
                "ok": ret == 0,
                "action": "tgkill",
                "tgid": int(pid),
                "tid": int(tid),
                "signal": int(signal),
                "ret": ret,
            }
        )
    except Exception as exc:
        return format_error(exc)
