from src.app import mcp
from src import process as proc_module
import asyncio


@mcp.tool()
async def renef_watch_realtime(duration_seconds: int = 30) -> str:
    """
    Watches hook output in real-time from the agent socket.

    This is different from renef_watch which reads from logcat.
    This tool connects directly to the agent socket and streams
    hook output as it happens.

    Note: MCP tools are request-response, so this collects output
    for the specified duration then returns it all at once.

    Args:
        duration_seconds: How long to watch for output (default: 30, max: 120)

    Returns:
        Collected hook output during the watch period
    """
    await proc_module.ensure_started()

    # Clamp duration
    duration_seconds = min(max(duration_seconds, 5), 120)

    proc_module.process.stdin.write(b"watch\n")
    await proc_module.process.stdin.drain()

    # Collect output for duration
    output_lines = []
    start_time = asyncio.get_event_loop().time()

    while (asyncio.get_event_loop().time() - start_time) < duration_seconds:
        try:
            line = await asyncio.wait_for(
                proc_module.process.stdout.readline(),
                timeout=1.0
            )
            if line:
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    output_lines.append(decoded)
        except asyncio.TimeoutError:
            continue

    # Send a newline to exit watch mode
    proc_module.process.stdin.write(b"\n")
    await proc_module.process.stdin.drain()

    # Drain any remaining output
    try:
        remaining = await asyncio.wait_for(
            proc_module.read_until_prompt(timeout=2.0),
            timeout=3.0
        )
        if remaining.strip():
            output_lines.append(remaining.strip())
    except:
        pass

    if output_lines:
        return "\n".join(output_lines)
    else:
        return f"No hook output received during {duration_seconds}s watch period."
