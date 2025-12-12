import asyncio
from src.app import mcp
from src.tools.server.renef_server_kill import renef_server_kill
from src.tools.server.renef_server_start import renef_server_start


@mcp.tool()
async def renef_server_restart() -> str:
    """
    Restarts renef_server on the connected Android device.

    Kills the existing process (if running) and starts a new one.

    Returns:
        Restart status message
    """
    results = []

    # Kill existing
    kill_result = await renef_server_kill()
    results.append(f"Kill: {kill_result}")

    # Small delay
    await asyncio.sleep(0.3)

    # Start new
    start_result = await renef_server_start()
    results.append(f"Start: {start_result}")

    return "\n".join(results)
