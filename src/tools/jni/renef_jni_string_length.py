from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_string_length(ref: str) -> str:
    """
    Gets the length of a Java String.

    Args:
        ref: JNI reference to Java String (e.g., '0x12345678')

    Returns:
        String length as integer
    """
    await proc_module.ensure_started()

    lua_code = f'local len = Jni.getStringLength({ref}); print(len)'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
