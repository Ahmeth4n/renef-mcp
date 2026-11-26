import re

from src.app import mcp
from src.session import format_error, run_adb, to_json


@mcp.tool()
async def adb_app(
    action: str,
    package_name: str = "",
    activity: str = "",
    filter: str = "",
) -> str:
    """Inspect, list, start, or force-stop Android apps via ADB.

    Actions:
    - `current`: Get currently focused app (package, activity, PID, UID)
    - `list`: List installed packages via `pm list packages` (optional substring `filter`)
    - `start`: Launch an app via `am start` (optional `activity`)
    - `start_monkey`: Launch an app via `monkey -p <package_name> -c LAUNCHER 1`
    - `stop`: Force-stop an app via `am force-stop <package_name>`

    Args:
        action: "current", "list", "start", "start_monkey", or "stop"
        package_name: Android package name (required for "start", "start_monkey", "stop")
        activity: Optional activity name for `action="start"`
        filter: Optional case-insensitive substring filter for `action="list"`

    Returns:
        JSON result with app information or command output
    """
    try:
        act = action.strip().lower()
        if act not in ("current", "list", "start", "start_monkey", "stop"):
            return "ERROR: action must be 'current', 'list', 'start', 'start_monkey', or 'stop'"

        if act == "current":
            _, focus_out = await run_adb(
                "shell", "dumpsys window | grep -A 3 'mCurrentFocus'", timeout=15.0
            )
            _, recents_out = await run_adb(
                "shell", "dumpsys activity recents | grep 'Recent #0' -A 10", timeout=15.0
            )
            pkg = None
            act_name = None
            focus_match = re.search(
                r"mCurrentFocus=Window\{[^\s]+ u\d+ ([^/]+)/([^}]+)\}", focus_out
            )
            if focus_match:
                pkg = focus_match.group(1)
                act_name = focus_match.group(2)

            pid = None
            uid = None
            pid_match = re.search(
                r"mRootProcess=ProcessRecord\{[^\s]+ (\d+):([^/]+)/([^}]+)\}", recents_out
            )
            if pid_match:
                pid = int(pid_match.group(1))
                uid = pid_match.group(3)
            elif pkg:
                _, pidof_out = await run_adb("shell", "pidof", "-s", pkg, timeout=10.0)
                if pidof_out.strip().isdigit():
                    pid = int(pidof_out.strip())

            return to_json(
                {
                    "ok": True,
                    "package": pkg,
                    "activity": act_name,
                    "pid": pid,
                    "uid": uid,
                    "status": "focused" if pkg else "unknown",
                }
            )

        if act == "list":
            rc, out = await run_adb("shell", "pm", "list", "packages", timeout=20.0)
            packages = [
                line.replace("package:", "").strip()
                for line in out.splitlines()
                if line.startswith("package:")
            ]
            if filter.strip():
                flt = filter.strip().lower()
                packages = [p for p in packages if flt in p.lower()]
            packages.sort()
            return to_json({"ok": rc == 0, "count": len(packages), "packages": packages})

        pkg = package_name.strip()
        if not pkg:
            return f"ERROR: package_name is required for action='{act}'"

        if act == "start":
            if activity.strip():
                cmd = ("shell", "am", "start", "-n", f"{pkg}/{activity.strip()}")
                rc, out = await run_adb(*cmd, timeout=20.0)
            else:
                # Resolve launcher activity first; fall back to monkey if unresolved
                rc_res, comp = await run_adb(
                    "shell", "cmd", "package", "resolve-activity", "--brief", pkg, timeout=15.0
                )
                component = ""
                if rc_res == 0 and comp:
                    for ln in reversed(comp.splitlines()):
                        if "/" in ln and not ln.startswith("priority"):
                            component = ln.strip()
                            break
                if component:
                    rc, out = await run_adb("shell", "am", "start", "-n", component, timeout=20.0)
                else:
                    rc, out = await run_adb(
                        "shell",
                        "monkey",
                        "-p",
                        pkg,
                        "-c",
                        "android.intent.category.LAUNCHER",
                        "1",
                        timeout=20.0,
                    )
            return to_json({"ok": rc == 0, "action": "start", "package": pkg, "output": out})

        if act == "start_monkey":
            rc, out = await run_adb(
                "shell",
                "monkey",
                "-p",
                pkg,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
                timeout=20.0,
            )
            return to_json({"ok": rc == 0, "action": "start_monkey", "package": pkg, "output": out})

        # stop
        rc, out = await run_adb("shell", "am", "force-stop", pkg, timeout=15.0)
        return to_json({"ok": rc == 0, "action": "stop", "package": pkg, "output": out or "stopped"})
    except Exception as exc:
        return format_error(exc)
