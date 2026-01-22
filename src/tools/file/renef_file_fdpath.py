from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_file_fdpath(fd: int) -> str:
    """
    Gets the file path for an open file descriptor.

    Reads /proc/self/fd/{fd} to determine what file the descriptor points to.

    Args:
        fd: File descriptor number (e.g., 3, 4, 5)

    Returns:
        File path, or 'nil' if fd is invalid
    """
    await proc_module.ensure_started()

    lua_code = f'local path = File.fdpath({fd}); print(path or "nil")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
