from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_jni_type_boolean(value: bool) -> str:
    """
    Creates a typed boolean wrapper for JNI hook arguments.

    This is used when you need to pass a specific type to a hooked Java method.
    Returns a Lua table with {__jni_type="boolean", value=<value>}.

    Args:
        value: The boolean value to wrap (True/False)

    Returns:
        Lua table representation as string
    """
    await proc_module.ensure_started()

    lua_val = "true" if value else "false"
    lua_code = f'local t = JNI.boolean({lua_val}); print(string.format("{{__jni_type=\\"%s\\", value=%s}}", t.__jni_type, tostring(t.value)))'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
