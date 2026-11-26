import asyncio

from src.app import mcp
from src.session import (
    ANDROID_BIN_DIR,
    DEVICE_AGENT_PATH,
    DEVICE_DEFAULT_SOCKET,
    DEVICE_LOG_PATH,
    DEVICE_SERVER_PATH,
    format_error,
    manager,
    run_adb,
    to_json,
)


async def _get_server_pid() -> str:
    rc, out = await run_adb("shell", "pidof", "renef_server", timeout=10.0)
    return out.strip() if rc == 0 else ""


async def _do_deploy() -> dict:
    server_bin = ANDROID_BIN_DIR / "renef_server"
    agent_bin = ANDROID_BIN_DIR / "libagent.so"
    if not server_bin.is_file() or not agent_bin.is_file():
        return {
            "ok": False,
            "error": f"Android v0.4.0 binaries not found in {ANDROID_BIN_DIR}",
        }

    # Remove existing files as root first: once libagent.so has chcon app_data_file,
    # adbd (u:r:adbd:s0) gets Permission denied trying to stat/overwrite it on redeploy.
    await run_adb(
        "shell",
        "su",
        "-c",
        f"rm -f {DEVICE_AGENT_PATH}",
        timeout=10.0,
    )

    rc_srv, out_srv = await run_adb("push", str(server_bin), DEVICE_SERVER_PATH, timeout=60.0)
    if rc_srv != 0 and ("Permission denied" in out_srv or "Text file busy" in out_srv):
        await run_adb("shell", "su", "-c", f"pkill -9 renef_server; rm -f {DEVICE_SERVER_PATH}", timeout=10.0)
        rc_srv, out_srv = await run_adb("push", str(server_bin), DEVICE_SERVER_PATH, timeout=60.0)
    rc_agt, out_agt = await run_adb("push", str(agent_bin), DEVICE_AGENT_PATH, timeout=60.0)
    await run_adb("shell", "chmod", "+x", DEVICE_SERVER_PATH, timeout=10.0)
    await run_adb("shell", "chmod", "777", DEVICE_AGENT_PATH, timeout=10.0)
    rc_sel, out_sel = await run_adb(
        "shell",
        "su",
        "-c",
        f"chcon u:object_r:app_data_file:s0 {DEVICE_AGENT_PATH}",
        timeout=10.0,
    )
    return {
        "ok": rc_srv == 0 and rc_agt == 0,
        "action": "deploy",
        "renef_server": {"path": DEVICE_SERVER_PATH, "ok": rc_srv == 0, "output": out_srv},
        "libagent": {"path": DEVICE_AGENT_PATH, "ok": rc_agt == 0, "output": out_agt},
        "selinux_chcon": {"ok": rc_sel == 0, "output": out_sel},
    }


async def _do_start() -> dict:
    existing = await _get_server_pid()
    if existing:
        await run_adb("forward", f"tcp:{manager.port}", DEVICE_DEFAULT_SOCKET, timeout=10.0)
        return {
            "ok": True,
            "action": "start",
            "already_running": True,
            "pid": existing,
            "port": manager.port,
        }

    rc_fwd, out_fwd = await run_adb(
        "forward", f"tcp:{manager.port}", DEVICE_DEFAULT_SOCKET, timeout=10.0
    )
    await run_adb(
        "shell",
        "su",
        "-c",
        f"nohup {DEVICE_SERVER_PATH} > {DEVICE_LOG_PATH} 2>&1 &",
        timeout=10.0,
    )
    await asyncio.sleep(0.8)
    pid = await _get_server_pid()
    return {
        "ok": bool(pid),
        "action": "start",
        "pid": pid or None,
        "port_forward": {"port": manager.port, "ok": rc_fwd == 0, "output": out_fwd},
    }


async def _do_kill() -> dict:
    manager.reset_session()
    pid = await _get_server_pid()
    if not pid:
        return {"ok": True, "action": "kill", "message": "renef_server is not running"}

    rc, _ = await run_adb("shell", "su", "-c", f"kill -9 {pid}", timeout=10.0)
    if rc != 0:
        await run_adb("shell", "kill", "-9", *pid.split(), timeout=10.0)
    await asyncio.sleep(0.3)
    remaining = await _get_server_pid()
    return {
        "ok": not bool(remaining),
        "action": "kill",
        "previous_pid": pid,
        "remaining_pid": remaining or None,
    }


@mcp.tool()
async def renef_server(
    action: str = "status",
    lines: int = 100,
    clear_logs: bool = False,
) -> str:
    """Manage the on-device Android `renef_server` daemon and `libagent.so` deployment.

    Uses Renef v0.4.0 device paths:
    - `/data/local/tmp/renef_server` (`chmod +x`)
    - `/data/local/tmp/libagent.so` (`chmod 777` + `chcon u:object_r:app_data_file:s0`)

    Actions:
    - `status` (default): Check deployment of both binaries and whether `renef_server` is running
    - `deploy`: Push v0.4.0 `renef_server` and `libagent.so` to device with proper permissions/SELinux context
    - `start`: Setup ADB port forward (`tcp:<port>`) and start `renef_server` in background as root
    - `kill`: Stop running `renef_server` and close local session
    - `restart`: Kill and start `renef_server`
    - `logs`: Show tail of `/data/local/tmp/renef.log` (optionally truncate with `clear_logs=True`)

    Args:
        action: "status", "deploy", "start", "kill", "restart", or "logs"
        lines: Number of log lines for `action="logs"` (default: 100)
        clear_logs: If True with `action="logs"`, clear the log file after reading

    Returns:
        JSON status or server logs
    """
    try:
        act = action.strip().lower()
        if act not in ("status", "deploy", "start", "kill", "restart", "logs"):
            return "ERROR: action must be 'status', 'deploy', 'start', 'kill', 'restart', or 'logs'"

        if act == "deploy":
            return to_json(await _do_deploy())

        if act == "start":
            return to_json(await _do_start())

        if act == "kill":
            return to_json(await _do_kill())

        if act == "restart":
            kill_res = await _do_kill()
            await asyncio.sleep(0.3)
            start_res = await _do_start()
            return to_json(
                {
                    "ok": bool(start_res.get("ok")),
                    "action": "restart",
                    "kill": kill_res,
                    "start": start_res,
                }
            )

        if act == "logs":
            n = max(1, min(int(lines), 2000))
            shell_cmd = (
                f"tail -n {n} {DEVICE_LOG_PATH} && > {DEVICE_LOG_PATH}"
                if clear_logs
                else f"tail -n {n} {DEVICE_LOG_PATH}"
            )
            rc, out = await run_adb("shell", "su", "-c", shell_cmd, timeout=15.0)
            if rc != 0 and not out:
                rc, out = await run_adb("shell", f"tail -n {n} {DEVICE_LOG_PATH}", timeout=15.0)
            return out or "No logs available (log file empty or does not exist)."

        # status
        _, srv_out = await run_adb(
            "shell", f"test -f {DEVICE_SERVER_PATH} && echo exists", timeout=10.0
        )
        _, agt_out = await run_adb(
            "shell", f"test -f {DEVICE_AGENT_PATH} && echo exists", timeout=10.0
        )
        pid = await _get_server_pid()
        return to_json(
            {
                "ok": True,
                "action": "status",
                "renef_server_deployed": "exists" in srv_out,
                "renef_server_path": DEVICE_SERVER_PATH,
                "libagent_deployed": "exists" in agt_out,
                "libagent_path": DEVICE_AGENT_PATH,
                "running": bool(pid),
                "pid": pid or None,
                "configured_port": manager.port,
            }
        )
    except Exception as exc:
        return format_error(exc)
