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


@mcp.tool()
async def renef_reset(
    mode: str = "session",
    redeploy: bool = False,
    kill_app: str = "",
) -> str:
    """Reset the Renef session or perform a full device/server hard reset.

    Modes:
    - `session` (default): Closes the local TCP connection and clears session state. Fast and safe.
    - `hard`: Closes local session, kills target app (if specified/tracked), kills and restarts
      `renef_server` on the Android device, refreshes ADB port forwarding, optionally redeploys
      v0.4.0 binaries (`renef_server` + `/data/local/tmp/libagent.so`), and verifies with `ping`.

    Args:
        mode: Reset mode - "session" (default) or "hard"
        redeploy: (hard mode only) Re-push renef_server and libagent.so to device
        kill_app: (hard mode only) Package name or PID to force-stop/kill

    Returns:
        JSON status with step-by-step reset results
    """
    try:
        mode_norm = mode.strip().lower()
        if mode_norm not in ("session", "hard"):
            return "ERROR: mode must be 'session' or 'hard'"

        tracked_pid = manager.current_target_pid
        tracked_pkg = manager.current_target_package
        manager.reset_session()

        if mode_norm == "session":
            return to_json(
                {
                    "ok": True,
                    "mode": "session",
                    "message": "Local Renef TCP connection and session state reset.",
                }
            )

        steps = [{"step": "reset_local_session", "ok": True}]

        # 1. Stop target app if specified or previously tracked
        target = kill_app.strip() or tracked_pkg or (str(tracked_pid) if tracked_pid else "")
        if target:
            if target.isdigit():
                rc, out = await run_adb("shell", "su", "-c", f"kill -9 {target}", timeout=10.0)
                if rc != 0:
                    rc, out = await run_adb("shell", "kill", "-9", target, timeout=10.0)
            else:
                rc, out = await run_adb("shell", "am", "force-stop", target, timeout=15.0)
            steps.append({"step": f"stop_target({target})", "ok": rc == 0, "output": out})

        # 2. Kill renef_server on device
        rc, out = await run_adb("shell", "su", "-c", "pkill -9 renef_server", timeout=10.0)
        if rc != 0:
            await run_adb("shell", "pkill", "-9", "renef_server", timeout=10.0)
        steps.append({"step": "kill_renef_server", "ok": True})

        # 3. Clear port forward for configured port
        await run_adb("forward", "--remove", f"tcp:{manager.port}", timeout=10.0)
        steps.append({"step": "clear_port_forward", "ok": True})

        # 4. Optional redeploy (Renef v0.4.0 paths: /data/local/tmp/renef_server & /data/local/tmp/libagent.so)
        if redeploy:
            server_bin = ANDROID_BIN_DIR / "renef_server"
            agent_bin = ANDROID_BIN_DIR / "libagent.so"
            if not server_bin.is_file() or not agent_bin.is_file():
                steps.append(
                    {
                        "step": "redeploy",
                        "ok": False,
                        "output": f"Missing Android binaries in {ANDROID_BIN_DIR}",
                    }
                )
            else:
                await run_adb(
                    "shell",
                    "su",
                    "-c",
                    f"rm -f {DEVICE_AGENT_PATH} {DEVICE_SERVER_PATH}",
                    timeout=10.0,
                )
                rc1, out1 = await run_adb("push", str(server_bin), DEVICE_SERVER_PATH, timeout=60.0)
                rc2, out2 = await run_adb("push", str(agent_bin), DEVICE_AGENT_PATH, timeout=60.0)
                await run_adb("shell", "chmod", "+x", DEVICE_SERVER_PATH, timeout=10.0)
                await run_adb("shell", "chmod", "777", DEVICE_AGENT_PATH, timeout=10.0)
                await run_adb(
                    "shell",
                    "su",
                    "-c",
                    f"chcon u:object_r:app_data_file:s0 {DEVICE_AGENT_PATH}",
                    timeout=10.0,
                )
                steps.append(
                    {
                        "step": "redeploy",
                        "ok": rc1 == 0 and rc2 == 0,
                        "output": f"{out1} | {out2}",
                    }
                )

        # 5. Start renef_server
        await run_adb(
            "shell",
            "su",
            "-c",
            f"nohup {DEVICE_SERVER_PATH} > {DEVICE_LOG_PATH} 2>&1 &",
            timeout=10.0,
        )
        await asyncio.sleep(1.0)
        rc_pid, pid_out = await run_adb("shell", "pidof", "renef_server", timeout=10.0)
        server_running = rc_pid == 0 and bool(pid_out.strip())
        steps.append(
            {
                "step": "start_renef_server",
                "ok": server_running,
                "pid": pid_out.strip() or None,
            }
        )

        # 6. Restore port forward
        rc_fwd, out_fwd = await run_adb(
            "forward", f"tcp:{manager.port}", DEVICE_DEFAULT_SOCKET, timeout=10.0
        )
        steps.append({"step": "port_forward", "ok": rc_fwd == 0, "output": out_fwd})

        # 7. Verify via ping
        ping_ok = False
        ping_err = None
        try:
            ping_ok = await manager.call(lambda: manager.get_client().ping())
        except Exception as exc:
            ping_err = str(exc)
        steps.append({"step": "ping", "ok": ping_ok, "error": ping_err})

        return to_json({"ok": server_running and ping_ok, "mode": "hard", "steps": steps})
    except Exception as exc:
        return format_error(exc)
