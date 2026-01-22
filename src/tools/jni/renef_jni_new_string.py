from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_new_string(value: str) -> str:
    """
    Creates a new Java String object in the target process.

    Args:
        value: String content to create

    Returns:
        Raw pointer to Java String object (as hex), for use with other JNI tools
    """
    await proc_module.ensure_started()

    # Escape quotes in the string
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    lua_code = f'local ptr = Jni.newStringUTF("{escaped}"); print(string.format("0x%x", ptr))'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
