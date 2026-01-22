from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_mem_search_json(pattern: str) -> str:
    """
    Searches memory for a hex pattern and returns structured JSON results.

    Uses the CLI 'msj' command which returns JSON format suitable for parsing.

    Args:
        pattern: Hex pattern to search (e.g., 'DEADBEEF', '4A617661')

    Returns:
        JSON object with:
        - success: boolean
        - count: number of matches
        - results: array of {library, offset, address, hex, ascii}
    """
    await proc_module.ensure_started()

    cmd = f"msj {pattern}\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
