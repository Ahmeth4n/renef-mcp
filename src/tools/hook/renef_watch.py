import asyncio
from src.app import mcp


@mcp.tool()
async def renef_watch(duration_seconds: int = 10, clear: bool = True) -> str:
    """
    Collects hook output from Android logcat.

    The Lua print() function automatically writes to logcat (tag: RENEF_LUA).
    This tool reads those logs, bypassing the socket connection issues.

    Args:
        duration_seconds: How long to wait for output (default: 10 seconds)
        clear: Clear logcat buffer before watching (default: True)

    Returns:
        Captured hook output from logcat
    """
    if clear:
        # Clear logcat buffer first
        proc = await asyncio.create_subprocess_exec(
            "adb", "logcat", "-c",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await proc.communicate()

    # Wait for specified duration to collect output
    await asyncio.sleep(duration_seconds)

    # Read RENEF_LUA tagged logs
    proc = await asyncio.create_subprocess_exec(
        "adb", "logcat", "-d", "-s", "RENEF_LUA:I",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()

    # Parse and clean output
    lines = stdout.decode('utf-8', errors='replace').split('\n')
    output = []

    for line in lines:
        # Skip empty lines and header
        if not line.strip() or line.startswith('-----'):
            continue

        # Extract [SCRIPT] messages (from print() calls in Lua)
        if "[SCRIPT]" in line:
            msg = line.split("[SCRIPT]", 1)[1].strip()
            output.append(msg)
        # Also capture [CLI_SEND] for debugging
        elif "[CLI_SEND]" in line:
            msg = line.split("[CLI_SEND]", 1)[1].strip()
            output.append(f"[send] {msg}")

    if not output:
        return "No hook output in logcat"

    return '\n'.join(output)
