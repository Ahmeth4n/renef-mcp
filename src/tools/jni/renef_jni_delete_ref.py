from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_delete_ref(ref: str) -> str:
    """
    Deletes a JNI global reference to prevent memory leaks.

    Args:
        ref: JNI global reference to delete (e.g., '0x12345678')

    Returns:
        Confirmation message
    """
    await proc_module.ensure_started()

    lua_code = f'Jni.deleteGlobalRef({ref}); print("deleted")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
