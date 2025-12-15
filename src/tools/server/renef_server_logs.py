import asyncio
from src.app import mcp


@mcp.tool()
async def renef_server_logs(lines: int = 100, clear: bool = False) -> str:
    """
    Shows renef_server logs from the Android device.

    Args:
        lines: Number of log lines to show (default: 100)
        clear: If True, clears the log file after reading

    Returns:
        Server log content
    """
    if clear:
        # Read and then clear
        proc = await asyncio.create_subprocess_exec(
            "adb", "shell", "su", "-c",
            f"cat /data/local/tmp/renef.log && > /data/local/tmp/renef.log",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    else:
        proc = await asyncio.create_subprocess_exec(
            "adb", "shell", "su", "-c",
            f"tail -n {lines} /data/local/tmp/renef.log",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

    stdout, _ = await proc.communicate()
    output = stdout.decode('utf-8', errors='replace').strip()

    if not output:
        return "No logs available (log file empty or doesn't exist)"

    return output
