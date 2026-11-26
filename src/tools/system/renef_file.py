from src.app import mcp
from src.session import format_error, lua_quote, manager, parse_address, to_json, to_lua


@mcp.tool()
async def renef_file(
    action: str,
    path: str = "",
    fd: int = -1,
    address: str = "",
    size: int = 0,
) -> str:
    """Filesystem operations executed inside the target process context (`File.*` API).

    Runs with the target app's UID/SELinux context, so it can read the app's private data
    files (`/data/data/<pkg>/...`) and dump in-memory payloads directly to disk.

    Actions:
    - `read`: Read file contents -> `File.read(path)`
    - `write`: Dump target memory `[address, address+size)` to a device file (max 100MB) -> `File.write(path, addr, size)`
    - `exists`: Check if file exists -> `File.exists(path)`
    - `readlink`: Resolve a symlink target -> `File.readlink(path)`
    - `fdpath`: Get filesystem path for an open file descriptor (`/proc/self/fd/<fd>`) -> `File.fdpath(fd)`

    Args:
        action: "read", "write", "exists", "readlink", or "fdpath"
        path: File path on device (required for all actions except "fdpath")
        fd: File descriptor number (required for "fdpath")
        address: Source memory address in target (required for "write")
        size: Number of bytes to dump from memory (required for "write", max 100MB)

    Returns:
        JSON object with operation result
    """
    try:
        act = action.strip().lower()
        if act not in ("read", "write", "exists", "readlink", "fdpath"):
            return "ERROR: action must be 'read', 'write', 'exists', 'readlink', or 'fdpath'"

        if act == "fdpath":
            if fd < 0:
                return "ERROR: fd must be a non-negative integer"

            def _fdpath():
                session = manager.require_session()
                return session.File.fdpath(int(fd))

            target = await manager.call(_fdpath)
            return to_json({"ok": True, "action": "fdpath", "fd": int(fd), "path": target})

        p = path.strip()
        if not p:
            return f"ERROR: path is required for action='{act}'"

        if act == "exists":
            def _exists():
                session = manager.require_session()
                return session.File.exists(p)

            exists = await manager.call(_exists)
            return to_json({"ok": True, "action": "exists", "path": p, "exists": exists})

        if act == "readlink":
            def _readlink():
                session = manager.require_session()
                return session.File.readlink(p)

            target = await manager.call(_readlink)
            return to_json({"ok": True, "action": "readlink", "path": p, "target": target})

        if act == "read":
            def _read():
                session = manager.require_session()
                return session.File.read(p)

            content = await manager.call(_read)
            return to_json({"ok": True, "action": "read", "path": p, "content": content})

        # write (dump target memory to device file, surfacing exact agent error if any)
        addr = parse_address(address)
        if addr == 0:
            return "ERROR: address must be non-zero for action='write'"
        if size <= 0 or size > 100 * 1024 * 1024:
            return "ERROR: size must be between 1 and 104857600 (100MB) for action='write'"

        expr = (
            "(function() "
            f"local ok, err = File.write({lua_quote(p)}, {to_lua(addr)}, {int(size)}); "
            'if not ok then error(tostring(err or "File.write failed"), 0) end; '
            "return true end)()"
        )

        def _write():
            session = manager.require_session()
            return session.rpc(expr, timeout=60.0)

        ok = await manager.call(_write)
        return to_json(
            {
                "ok": bool(ok),
                "action": "write",
                "path": p,
                "address_hex": f"0x{addr:x}",
                "size": int(size),
            }
        )
    except Exception as exc:
        return format_error(exc)
