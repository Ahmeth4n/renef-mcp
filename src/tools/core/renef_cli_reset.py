from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_cli_reset() -> str:
    """
    Resets the renef CLI process by killing any stuck process and starting fresh.
    Use this when commands are timing out or the CLI is unresponsive.

    Returns:
        Reset status
    """
    results = []

    # Kill existing process if any
    if proc_module.process is not None:
        try:
            proc_module.process.kill()
            await proc_module.process.wait()
            results.append("✓ Killed stuck CLI process")
        except Exception as e:
            results.append(f"? Kill attempt: {e}")

    # Reset global process to None
    proc_module.process = None
    results.append("✓ Reset process state")

    # Start fresh
    try:
        await proc_module.ensure_started()
        results.append("✓ Started fresh CLI process")
    except Exception as e:
        results.append(f"✗ Failed to start: {e}")

    return "\n".join(results)
