import asyncio
from src.app import mcp


@mcp.tool()
async def renef_port_forward_status() -> str:
    """
    Shows current ADB port forwarding rules.

    Returns:
        List of active port forwards
    """
    proc = await asyncio.create_subprocess_exec(
        "adb", "forward", "--list",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace").strip()

    if not output:
        return "No port forwards active"

    # Format output nicely
    lines = output.splitlines()
    results = ["Active port forwards:"]
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            device, local, remote = parts[0], parts[1], parts[2]
            results.append(f"  {local} -> {remote} ({device})")
        else:
            results.append(f"  {line}")

    return "\n".join(results)
