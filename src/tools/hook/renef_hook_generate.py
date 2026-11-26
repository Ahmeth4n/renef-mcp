from src.app import mcp
from src.session import format_error, manager


@mcp.tool()
async def renef_hook_generate(lib_name: str = "", offset_or_symbol: str = "") -> str:
    """Generate a Renef Lua hook template using the server's `hookgen` command.

    Examples:
    - `renef_hook_generate("libnative.so", "0x1234")` — template for offset
    - `renef_hook_generate("libc.so", "malloc")` — template for symbol in library
    - `renef_hook_generate("malloc")` — search symbol across loaded libraries

    Args:
        lib_name: Library name, or symbol name if `offset_or_symbol` is omitted
        offset_or_symbol: Optional hex offset or symbol name inside `lib_name`

    Returns:
        Generated Lua hook template
    """
    try:
        a = lib_name.strip()
        b = offset_or_symbol.strip()
        if a and b:
            cmd = f"hookgen {a} {b}"
        elif a:
            cmd = f"hookgen {a}"
        else:
            cmd = "hookgen"

        def _gen():
            session = manager.get_session()
            if session is not None:
                return session.command(cmd).strip()
            client = manager.get_client()
            return client._text(cmd).strip()

        return await manager.call(_gen)
    except Exception as exc:
        return format_error(exc)
