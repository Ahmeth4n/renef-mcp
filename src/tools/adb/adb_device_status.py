from src.app import mcp
from src.session import format_error, run_adb, to_json


@mcp.tool()
async def adb_device_status(selinux_action: str = "") -> str:
    """Check Android device root & SELinux status, and optionally toggle SELinux mode.

    Args:
        selinux_action: Optional - "disable" (Permissive / setenforce 0) or
                        "enable" (Enforcing / setenforce 1). Leave empty to inspect only.

    Returns:
        JSON report with root status, su/Magisk checks, and SELinux state
    """
    try:
        sel_act = selinux_action.strip().lower()
        if sel_act and sel_act not in ("enable", "disable"):
            return "ERROR: selinux_action must be '', 'enable', or 'disable'"

        selinux_change = None
        if sel_act:
            val = "0" if sel_act == "disable" else "1"
            rc, out = await run_adb("shell", "su", "-c", f"setenforce {val}", timeout=10.0)
            if rc != 0:
                rc, out = await run_adb("shell", "setenforce", val, timeout=10.0)
            selinux_change = {"requested": sel_act, "rc": rc, "output": out}

        _, whoami = await run_adb("shell", "whoami", timeout=10.0)
        _, su_id = await run_adb("shell", "su", "-c", "id", timeout=10.0)
        _, magisk = await run_adb("shell", "magisk", "-v", timeout=10.0)
        _, selinux = await run_adb("shell", "getenforce", timeout=10.0)

        su_working = "uid=0" in su_id
        is_rooted = whoami == "root" or su_working
        magisk_ver = magisk if magisk and "not found" not in magisk.lower() else None

        result = {
            "ok": True,
            "rooted": is_rooted,
            "adb_user": whoami,
            "su_working": su_working,
            "magisk": magisk_ver,
            "selinux": selinux,
        }
        if selinux_change is not None:
            expected = "Permissive" if sel_act == "disable" else "Enforcing"
            selinux_change["applied"] = selinux == expected
            result["selinux_change"] = selinux_change
        return to_json(result)
    except Exception as exc:
        return format_error(exc)
