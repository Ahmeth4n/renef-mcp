from src.app import mcp
from src import process as proc_module


async def zero_copy_multiline_exec(lua_code: str) -> str:
    """
    Internal function to execute multiline Lua code via hex encoding.
    Zero-copy: no temp files, single line transmission.

    Args:
        lua_code: Multiline Lua code to execute

    Returns:
        Execution output
    """
    await proc_module.ensure_started()

    # Encode Lua code as hex string
    hex_str = lua_code.encode().hex()

    # Simple Lua hex decoder + load + execute
    cmd = f'exec local h="{hex_str}" local s="" for i=1,#h,2 do s=s..string.char(tonumber(h:sub(i,i+1),16)) end load(s)()\n'

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()


@mcp.tool()
async def renef_zero_copy_multiline_exec(lua_code: str) -> str:
    """
    Executes multiline Lua code in the target process using zero-copy hex encoding.

    This tool handles multiline Lua scripts by encoding them as hex,
    transmitting as a single line, and decoding/executing on the target.

    Args:
        lua_code: Multiline Lua code to execute

    Returns:
        Execution output
    """
    return await zero_copy_multiline_exec(lua_code)
