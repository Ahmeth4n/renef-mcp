from src.app import mcp
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_module_symbols(lib_name: str, filter: str = "") -> str:
    """
    Gets all symbols from a library's symbol table (.symtab), including internal symbols.

    Args:
        lib_name: Library name (e.g., 'linker64', 'libc.so')
        filter: Optional filter string to search symbol names

    Returns:
        List of symbols with their offsets, or nil if library not found/stripped
    """
    if filter:
        lua_code = f'''
local symbols = Module.symbols("{lib_name}")
if symbols then
    for _, sym in ipairs(symbols) do
        if sym.name:find("{filter}") then
            print(string.format("%s: 0x%x", sym.name, sym.offset))
        end
    end
else
    print("nil (library not found or stripped)")
end
'''
    else:
        lua_code = f'''
local symbols = Module.symbols("{lib_name}")
if symbols then
    for _, sym in ipairs(symbols) do
        print(string.format("%s: 0x%x", sym.name, sym.offset))
    end
else
    print("nil (library not found or stripped)")
end
'''

    return await zero_copy_multiline_exec(lua_code)
