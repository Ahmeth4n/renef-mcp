from src.app import mcp
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_module_exports(lib_name: str, filter: str = "") -> str:
    """
    Gets exported symbols from a library's dynamic symbol table (.dynsym).

    Args:
        lib_name: Library name (e.g., 'libc.so')
        filter: Optional filter string to search symbol names

    Returns:
        List of exported symbols with their offsets
    """
    if filter:
        lua_code = f'''
local exports = Module.exports("{lib_name}")
if exports then
    for _, sym in ipairs(exports) do
        if sym.name:find("{filter}") then
            print(string.format("%s: 0x%x", sym.name, sym.offset))
        end
    end
else
    print("nil")
end
'''
    else:
        lua_code = f'''
local exports = Module.exports("{lib_name}")
if exports then
    for _, sym in ipairs(exports) do
        print(string.format("%s: 0x%x", sym.name, sym.offset))
    end
else
    print("nil")
end
'''

    return await zero_copy_multiline_exec(lua_code)
