from src.app import mcp
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_hook_java(class_name: str, method_name: str, signature: str, log_args: bool = True) -> str:
    """
    Hooks a Java method via JNI.

    Args:
        class_name: Java class name with / separators (e.g., 'com/example/MainActivity')
        method_name: Method name (e.g., 'getSecret')
        signature: JNI type signature (e.g., '(Ljava/lang/String;)Ljava/lang/String;')
        log_args: If True, logs method arguments when called

    Returns:
        Hook installation result
    """
    if log_args:
        lua_code = f'''
hook("{class_name}", "{method_name}", "{signature}", {{
    onEnter = function(args)
        print("[Java Hook] {class_name}.{method_name} called")
        for i = 0, 10 do
            if args[i] then
                print(string.format("  arg[%d]: 0x%x", i, args[i]))
            end
        end
    end,
    onLeave = function(retval)
        print(string.format("  return: 0x%x", retval or 0))
    end
}})
print("Hook installed")
'''
    else:
        lua_code = f'''
hook("{class_name}", "{method_name}", "{signature}", {{
    onEnter = function(args) end,
    onLeave = function(retval) end
}})
print("Hook installed")
'''

    return await zero_copy_multiline_exec(lua_code)
