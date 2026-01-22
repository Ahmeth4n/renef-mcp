from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_file_exists(path: str) -> str:
    """
    Checks if a file exists in the target process filesystem.

    Args:
        path: Absolute path to check (e.g., '/system/bin/su')

    Returns:
        'true' or 'false'
    """
    await proc_module.ensure_started()

    lua_code = f'print(File.exists("{path}") and "true" or "false")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
