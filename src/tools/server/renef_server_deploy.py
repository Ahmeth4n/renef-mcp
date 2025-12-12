import asyncio
import os
from src.app import mcp


@mcp.tool()
async def renef_server_deploy() -> str:
    """
    Deploys renef_server and libagent.so to the connected Android device.

    Pushes:
        - renef_server -> /data/local/tmp/renef_server
        - libagent.so -> /data/local/tmp/.r

    Also makes renef_server executable.

    Returns:
        Deployment status message
    """
    # Android binaries are in bin/android/
    bin_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bin", "android")
    server_path = os.path.join(bin_dir, "renef_server")
    agent_path = os.path.join(bin_dir, "libagent.so")

    results = []

    # Push renef_server
    proc = await asyncio.create_subprocess_exec(
        "adb", "push", server_path, "/data/local/tmp/renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    results.append(f"renef_server: {stdout.decode('utf-8', errors='replace').strip()}")

    # Push libagent.so
    proc = await asyncio.create_subprocess_exec(
        "adb", "push", agent_path, "/data/local/tmp/.r",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    results.append(f"libagent.so: {stdout.decode('utf-8', errors='replace').strip()}")

    # Make renef_server executable
    proc = await asyncio.create_subprocess_exec(
        "adb", "shell", "chmod", "+x", "/data/local/tmp/renef_server",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    await proc.communicate()
    results.append("chmod +x: done")

    return "\n".join(results)
