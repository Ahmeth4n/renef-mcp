from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def run(command: str) -> str:
    """
    Sends a command to the CLI and returns the output.

    Args:
        command: The command to execute

    Returns:
        Command output
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(f"{command}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
