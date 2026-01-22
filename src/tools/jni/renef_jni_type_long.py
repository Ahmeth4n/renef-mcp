from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_type_long(value: int) -> str:
    """
    Creates a typed long wrapper for JNI hook arguments.

    This is used when you need to pass a specific type to a hooked Java method.
    Returns a Lua table with {__jni_type="long", value=<value>}.

    Args:
        value: The long integer value to wrap

    Returns:
        Lua table representation as string
    """
    await proc_module.ensure_started()

    lua_code = f'local t = JNI.long({value}); print(string.format("{{__jni_type=\\"%s\\", value=%d}}", t.__jni_type, t.value))'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
