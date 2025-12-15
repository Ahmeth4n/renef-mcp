from src.app import mcp
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_mem_read(address: str, size: int) -> str:
    """
    Reads raw bytes from memory at the specified address.

    Args:
        address: Memory address (e.g., '0x7f8a1c2b0')
        size: Number of bytes to read (max 1MB)

    Returns:
        Raw bytes in hex format
    """
    lua_code = f'''
local data = Memory.read({address}, {size})
if data then
    local hex = ""
    for i = 1, #data do
        hex = hex .. string.format("%02x ", data:byte(i))
    end
    print(hex)
else
    print("nil")
end
'''

    return await zero_copy_multiline_exec(lua_code)
