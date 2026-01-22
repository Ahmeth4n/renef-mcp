from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_file_readlink(path: str) -> str:
    """
    Reads the target of a symbolic link.

    Args:
        path: Path to symlink (e.g., '/proc/self/exe')

    Returns:
        Symlink target path, or 'nil' if not a symlink
    """
    await proc_module.ensure_started()

    lua_code = f'local target = File.readlink("{path}"); print(target or "nil")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
