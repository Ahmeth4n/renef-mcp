from src.app import mcp
from src.session import format_error, manager


@mcp.tool()
async def renef_module_sections(lib_name: str) -> str:
    """List ELF sections of a loaded library (`sec <lib_name>`).

    Args:
        lib_name: Library name (e.g., "libnative.so", "libflutter.so")

    Returns:
        Formatted ELF section list from renef_server
    """
    try:
        lib = lib_name.strip()
        if not lib:
            return "ERROR: lib_name cannot be empty"

        def _sec():
            session = manager.require_session()
            return session.command(f"sec {lib}").strip()

        return await manager.call(_sec)
    except Exception as exc:
        return format_error(exc)
