from src.app import mcp
from src.session import format_error, manager, to_json


@mcp.tool()
async def renef_process(
    action: str = "info",
    filter: str = "",
    limit: int = 200,
) -> str:
    """Inspect target process memory ranges, threads, thread ID, and stack backtrace.

    Actions:
    - `info` (default): PID (`OS.getpid`), current agent thread ID (`Thread.id`), and thread count
    - `ranges`: Enumerate `/proc/self/maps` via `Process.enumerateRanges()` (optional substring `filter` on path or perms like `"r-xp"`)
    - `threads`: Enumerate all live thread IDs via `Process.enumerateThreads()`
    - `thread_id`: Current agent thread ID (`Thread.id()`)
    - `backtrace`: PAC-aware stack backtrace (`Thread.backtrace()`)

    Args:
        action: "info", "ranges", "threads", "thread_id", or "backtrace"
        filter: Optional substring filter for `action="ranges"` (matches path or perms)
        limit: Maximum entries for `action="ranges"` (default: 200)

    Returns:
        JSON object with requested process/thread data
    """
    try:
        act = action.strip().lower()
        if act not in ("info", "ranges", "threads", "thread_id", "backtrace"):
            return "ERROR: action must be 'info', 'ranges', 'threads', 'thread_id', or 'backtrace'"

        if act == "info":
            def _info():
                session = manager.require_session()
                pid = session.OS.getpid()
                tid = session.Thread.id()
                threads = session.Process.threads()
                return pid, tid, threads

            pid, tid, threads = await manager.call(_info)
            return to_json(
                {
                    "ok": True,
                    "pid": pid,
                    "current_thread_id": tid,
                    "thread_count": len(threads),
                    "threads": threads,
                }
            )

        if act == "ranges":
            cap = max(1, min(int(limit), 2000))

            def _ranges():
                session = manager.require_session()
                return session.Process.ranges()

            ranges = await manager.call(_ranges)
            if filter.strip():
                flt = filter.strip().lower()
                ranges = [
                    r
                    for r in ranges
                    if flt in r.path.lower() or flt in r.perms.lower()
                ]
            shown = ranges[:cap]
            return to_json(
                {
                    "ok": True,
                    "total": len(ranges),
                    "returned": len(shown),
                    "ranges": [
                        {
                            "start": r.start,
                            "start_hex": f"0x{r.start:x}",
                            "end": r.end,
                            "end_hex": f"0x{r.end:x}",
                            "size": r.size,
                            "perms": r.perms,
                            "path": r.path,
                        }
                        for r in shown
                    ],
                }
            )

        if act == "threads":
            def _threads():
                session = manager.require_session()
                return session.Process.threads()

            tids = await manager.call(_threads)
            return to_json({"ok": True, "count": len(tids), "threads": tids})

        if act == "thread_id":
            def _tid():
                session = manager.require_session()
                return session.Thread.id()

            tid = await manager.call(_tid)
            return to_json({"ok": True, "thread_id": tid})

        # backtrace
        def _bt():
            session = manager.require_session()
            return session.Thread.backtrace()

        frames = await manager.call(_bt)
        return to_json(
            {
                "ok": True,
                "frame_count": len(frames),
                "frames": [
                    {
                        "index": f.index,
                        "pc": f.pc,
                        "pc_hex": f"0x{f.pc:x}",
                        "module": f.module,
                        "offset_hex": f"0x{f.offset:x}",
                        "base_hex": f"0x{f.base:x}" if f.base else None,
                        "path": f.path,
                    }
                    for f in frames
                ],
            }
        )
    except Exception as exc:
        return format_error(exc)
