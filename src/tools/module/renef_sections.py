from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_sections(lib_name: str) -> str:
    """
    Lists ELF sections of a library.

    Args:
        lib_name: Name of the library (e.g., 'libnative.so', 'libflutter.so')

    Returns:
        List of ELF sections
    """
    await proc_module.ensure_started()

    proc_module.process.stdin.write(f"sec {lib_name}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
