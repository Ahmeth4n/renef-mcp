from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_watch(duration_seconds: int = 5) -> str:
    """
    Collects hook output for specified duration.

    NOTE: Does NOT send 'watch' command (blocks in MCP subprocess mode).
    Hooks print directly to stdout when triggered, so we just read any output.

    Args:
        duration_seconds: How long to watch for output (default: 5 seconds)

    Returns:
        Captured hook output
    """
    import asyncio

    await proc_module.ensure_started()

    # DO NOT send "watch" command - it blocks forever in subprocess mode!
    # CLI watch uses recv() on TCP socket, but MCP uses stdin/stdout pipes.
    # recv() doesn't work on pipes, so watch command hangs.
    # Instead, just read any hook output that appears on stdout.

    buffer = b""
    end_time = asyncio.get_event_loop().time() + duration_seconds

    while asyncio.get_event_loop().time() < end_time:
        try:
            chunk = await asyncio.wait_for(
                proc_module.process.stdout.read(1024),
                timeout=0.5
            )
            if chunk:
                buffer += chunk
        except asyncio.TimeoutError:
            continue
        except Exception:
            break

    if not buffer:
        return "No hook output captured"

    text = buffer.decode('utf-8', errors='replace')
    text = text.replace("renef> ", "")

    return text if text else "No hook output captured"
