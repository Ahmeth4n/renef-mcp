from src.app import mcp
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_thread_backtrace() -> str:
    """
    Gets the current thread's stack backtrace.

    Returns a table of stack frames with:
    - index: Frame number (1-based)
    - pc: Program counter address
    - symbol: Function name (if available)
    - module: Library name
    - path: Full library path
    - base: Library base address
    - offset: Offset from library base

    Returns:
        Formatted stack trace
    """
    lua_code = '''
local frames = Thread.backtrace()
if frames then
    for i, frame in ipairs(frames) do
        local pc_str = string.format("0x%x", frame.pc)
        local offset_str = frame.offset and string.format("+0x%x", frame.offset) or ""
        local symbol_str = frame.symbol and string.format(" (%s%s)", frame.symbol, offset_str) or ""
        print(string.format("#%02d pc %s  %s%s",
            frame.index,
            pc_str,
            frame.path or frame.module or "<unknown>",
            symbol_str))
    end
else
    print("nil")
end
'''
    return await zero_copy_multiline_exec(lua_code)
