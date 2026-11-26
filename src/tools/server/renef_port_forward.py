from src.app import mcp
from src.session import (
    DEVICE_DEFAULT_SOCKET,
    format_error,
    manager,
    run_adb,
    to_json,
)


@mcp.tool()
async def renef_port_forward(
    action: str = "status",
    local_port: int = 0,
    remote: str = "",
    gadget_pid: int = 0,
) -> str:
    """Manage ADB TCP port forwarding rules for `renef_server` or rootless gadget mode.

    Actions:
    - `status` (default): List all active ADB port forwards
    - `add`: Add `adb forward tcp:<local_port> <remote>` (defaults to configured port -> RuntimeInit UDS;
             or if `gadget_pid > 0`, forwards to `localabstract:renef_pl_<gadget_pid>`)
    - `remove`: Remove forwarding rule for `tcp:<local_port>`
    - `remove_all`: Remove all ADB port forwarding rules

    Args:
        action: "status", "add", "remove", or "remove_all"
        local_port: Local TCP port (0 = use configured RENEF_PORT / 1907)
        remote: Remote endpoint (default: "localabstract:com.android.internal.os.RuntimeInit",
                or e.g. "tcp:1907" when server runs with `--transport TCP`)
        gadget_pid: Optional PID for gadget mode (`localabstract:renef_pl_<pid>`)

    Returns:
        JSON status with active rules or operation result
    """
    try:
        act = action.strip().lower()
        if act not in ("status", "add", "remove", "remove_all"):
            return "ERROR: action must be 'status', 'add', 'remove', or 'remove_all'"

        port = int(local_port) if local_port > 0 else manager.port

        if act == "status":
            rc, out = await run_adb("forward", "--list", timeout=10.0)
            rules = []
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    rules.append({"device": parts[0], "local": parts[1], "remote": parts[2]})
            return to_json({"ok": rc == 0, "action": "status", "count": len(rules), "rules": rules})

        if act == "add":
            if gadget_pid > 0:
                target_remote = f"localabstract:renef_pl_{int(gadget_pid)}"
            else:
                target_remote = remote.strip() or DEVICE_DEFAULT_SOCKET
            rc, out = await run_adb("forward", f"tcp:{port}", target_remote, timeout=10.0)
            return to_json(
                {
                    "ok": rc == 0,
                    "action": "add",
                    "local": f"tcp:{port}",
                    "remote": target_remote,
                    "output": out,
                }
            )

        if act == "remove":
            rc, out = await run_adb("forward", "--remove", f"tcp:{port}", timeout=10.0)
            return to_json({"ok": rc == 0, "action": "remove", "local": f"tcp:{port}", "output": out})

        rc, out = await run_adb("forward", "--remove-all", timeout=10.0)
        return to_json({"ok": rc == 0, "action": "remove_all", "output": out})
    except Exception as exc:
        return format_error(exc)
