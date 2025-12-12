from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_hook_generate(lib_name: str = "", offset_or_symbol: str = "") -> str:
    """
    Generates a Lua hook template.

    Args:
        lib_name: Library name (e.g., 'libnative.so'). If only this is provided, searches symbol in all libs.
        offset_or_symbol: Hex offset (e.g., '0x1234') or symbol name

    Usage:
        renef_hook_generate("libnative.so", "0x1234")  - Generate hook for specific offset
        renef_hook_generate("libnative.so", "malloc")  - Generate hook for symbol in lib
        renef_hook_generate("malloc")                  - Search symbol in all libraries

    Returns:
        Generated hook template code
    """
    await proc_module.ensure_started()

    if lib_name and offset_or_symbol:
        cmd = f"hookgen {lib_name} {offset_or_symbol}\n"
    elif lib_name:
        cmd = f"hookgen {lib_name}\n"
    else:
        cmd = "hookgen\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
