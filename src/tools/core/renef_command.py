from src.app import mcp
from src.session import format_error, manager


@mcp.tool()
async def renef_command(command: str, timeout: float = 35.0) -> str:
    """Send a raw command directly to renef_server over the framed TCP transport.

    Works both with an active target session (e.g., `hooks`, `sec libc.so`, `md 0x... 64`)
    and for sessionless server commands (e.g., `ping`, `la`, `memdump <pid> --maps`).

    Args:
        command: Raw renef_server command string
        timeout: Reply timeout in seconds (default: 35.0)

    Returns:
        Raw text response from renef_server
    """
    try:
        cmd = command.strip()
        if not cmd:
            return "ERROR: command cannot be empty"

        def _send():
            session = manager.get_session()
            if session is not None:
                return session.command(cmd, timeout=timeout)
            client = manager.get_client()
            return client._text(cmd, timeout=timeout)

        return await manager.call(_send)
    except Exception as exc:
        return format_error(exc)
