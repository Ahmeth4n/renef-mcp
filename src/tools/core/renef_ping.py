from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_ping() -> str:
    """
    Pings the renef server to check connectivity.

    Returns:
        Ping response from renef
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(b"ping\n")
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
