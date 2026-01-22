from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_file_read(path: str) -> str:
    """
    Reads file contents from the target process filesystem.

    Args:
        path: Absolute path to file (e.g., '/data/data/com.app/shared_prefs/config.xml')

    Returns:
        File contents as string, or 'nil' if file cannot be read
    """
    await proc_module.ensure_started()

    lua_code = f'local content = File.read("{path}"); print(content or "nil")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
