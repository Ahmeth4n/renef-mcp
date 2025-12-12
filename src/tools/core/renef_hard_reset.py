import asyncio
import os
import signal
import subprocess
from src.app import mcp
from src import process as proc_module


def kill_adb_forcefully():
    """Kill ADB daemon forcefully using pkill/killall - doesn't hang"""
    try:
        subprocess.run(["pkill", "-9", "adb"], capture_output=True, timeout=5)
    except:
        pass
    try:
        subprocess.run(["killall", "-9", "adb"], capture_output=True, timeout=5)
    except:
        pass


def kill_renef_cli_forcefully():
    """Kill any stuck renef CLI processes"""
    try:
        # Kill any process with "renef" in the command line (matches all platform binaries)
        subprocess.run(["pkill", "-9", "-f", "renef"], capture_output=True, timeout=5)
    except:
        pass


async def run_adb_command(*args, timeout: int = 30) -> tuple[bool, str]:
    """Run ADB command with timeout, returns (success, output)"""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return True, stdout.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except:
            pass
        return False, "timeout"
    except Exception as e:
        return False, str(e)


@mcp.tool()
async def renef_hard_reset(redeploy: bool = False, kill_app: str = "") -> str:
    """
    Performs a complete hard reset of the renef environment.

    Steps:
    1. Kill local CLI process
    2. Restart ADB server (mandatory - before any ADB communication)
    3. Force-stop target app (if injected/corrupted)
    4. Kill renef_server on device
    5. Clear port forwards
    6. (Optional) Redeploy binaries
    7. Start renef_server
    8. Setup port forward
    9. Start fresh CLI
    10. Test with ping

    Args:
        redeploy: If True, re-push renef_server and libagent to device
        kill_app: Package name of app to force-stop (e.g., 'com.android.settings')

    Returns:
        Reset status with details of each step
    """
    results = []

    # 1. Kill local CLI process (both managed and any stuck ones)
    kill_renef_cli_forcefully()  # Kill any stuck CLI processes first
    if proc_module.process is not None:
        try:
            proc_module.process.kill()
            await proc_module.process.wait()
            results.append("1. ✓ Killed local CLI process")
        except Exception as e:
            results.append(f"1. ? Kill CLI: {e}")
    else:
        results.append("1. ✓ No local CLI process running")

    proc_module.process = None

    # 2. Restart ADB server (mandatory - forcefully kill first, never hangs)
    kill_adb_forcefully()
    await asyncio.sleep(1)

    # Start fresh ADB server
    ok2, _ = await run_adb_command("adb", "start-server", timeout=15)
    await asyncio.sleep(2)

    # Wait for device to come online
    ok3, _ = await run_adb_command("adb", "wait-for-device", timeout=30)
    await asyncio.sleep(1)

    results.append(f"2. {'✓' if ok2 and ok3 else '⚠'} Restart ADB server (force killed)")

    # 3. Force-stop target app (if specified or if we have a tracked target)
    target_to_kill = kill_app
    if not target_to_kill and proc_module.current_target_pid:
        # Kill by PID if we have a tracked target
        target_to_kill = str(proc_module.current_target_pid)

    if target_to_kill:
        if target_to_kill.isdigit():
            # Kill by PID
            ok, out = await run_adb_command("adb", "shell", "kill", "-9", target_to_kill)
            results.append(f"3. {'✓' if ok else '⚠'} Kill target PID {target_to_kill}")
        else:
            # Force-stop by package name
            ok, out = await run_adb_command("adb", "shell", "am", "force-stop", target_to_kill)
            results.append(f"3. {'✓' if ok else '⚠'} Force-stop {target_to_kill}")
        # Clear tracked target
        proc_module.current_target_pid = None
        proc_module.current_target_package = None
    else:
        results.append("3. ⏭ No target to kill")

    # 4. Kill renef_server on device
    ok, out = await run_adb_command("adb", "shell", "pkill", "-9", "renef_server")
    results.append(f"4. {'✓' if ok else '⚠'} Kill renef_server: {out if not ok else 'done'}")

    # 5. Clear port forwards
    ok, out = await run_adb_command("adb", "forward", "--remove-all")
    results.append(f"5. {'✓' if ok else '⚠'} Clear port forwards: {out if not ok else 'done'}")

    # 6. Optional: Redeploy binaries
    if redeploy:
        # Android binaries are in bin/android/
        bin_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bin", "android")
        server_path = os.path.join(bin_dir, "renef_server")
        agent_path = os.path.join(bin_dir, "libagent.so")

        ok1, _ = await run_adb_command("adb", "push", server_path, "/data/local/tmp/renef_server", timeout=60)
        ok2, _ = await run_adb_command("adb", "push", agent_path, "/data/local/tmp/.r", timeout=60)
        ok3, _ = await run_adb_command("adb", "shell", "chmod", "+x", "/data/local/tmp/renef_server")

        results.append(f"6. {'✓' if ok1 and ok2 and ok3 else '⚠'} Redeploy binaries")
    else:
        results.append("6. ⏭ Skipped redeploy")

    # 7. Start renef_server
    ok, _ = await run_adb_command("adb", "shell", "nohup", "/data/local/tmp/renef_server", ">/dev/null", "2>&1", "&")
    await asyncio.sleep(2)

    # Verify server started
    ok, pid = await run_adb_command("adb", "shell", "pidof", "renef_server")
    if ok and pid:
        results.append(f"7. ✓ Started renef_server (PID: {pid})")
    else:
        results.append(f"7. ✗ Failed to start renef_server: {pid}")

    # 8. Setup port forward
    ok, out = await run_adb_command("adb", "forward", "tcp:1907", "localabstract:com.android.internal.os.RuntimeInit")
    results.append(f"8. {'✓' if ok else '⚠'} Setup port forward: {out if not ok else 'tcp:1907'}")

    # 9. Start fresh CLI
    try:
        await proc_module.ensure_started()
        results.append("9. ✓ Started fresh CLI process")
    except Exception as e:
        results.append(f"9. ✗ Failed to start CLI: {e}")
        results.append("\n⚠ Hard reset incomplete!")
        return "\n".join(results)

    # 10. Test with ping
    try:
        proc_module.process.stdin.write(b"ping\n")
        await proc_module.process.stdin.drain()
        response = await asyncio.wait_for(proc_module.read_until_prompt(), timeout=15)

        if "pong" in response.lower():
            results.append("10. ✓ Ping successful - pong received")
        else:
            results.append(f"10. ? Ping response: {response[:100]}")
    except asyncio.TimeoutError:
        results.append("10. ✗ Ping timeout")
    except Exception as e:
        results.append(f"10. ✗ Ping error: {e}")

    results.append("\n✓ Hard reset complete!")
    return "\n".join(results)
