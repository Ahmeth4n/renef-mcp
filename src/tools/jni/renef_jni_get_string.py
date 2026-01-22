from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_get_string(ref: str) -> str:
    """
    Extracts the UTF-8 content from a Java String reference.

    Args:
        ref: JNI reference or raw pointer (e.g., '0x12345678')

    Returns:
        String content, or error message
    """
    await proc_module.ensure_started()

    lua_code = f'local str = Jni.getStringUTF({ref}); print(str or "nil")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
