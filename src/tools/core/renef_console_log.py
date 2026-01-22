from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_console_log(message: str) -> str:
    """
    Logs a message to Android logcat and CLI output.

    Uses the console.log() Lua function which writes to both
    logcat (ANDROID_LOG_INFO) and sends output to the CLI.

    Args:
        message: Message to log

    Returns:
        Confirmation or empty string
    """
    await proc_module.ensure_started()

    escaped = message.replace('\\', '\\\\').replace('"', '\\"')
    lua_code = f'console.log("{escaped}")'

    proc_module.process.stdin.write(f"exec {lua_code}\n".encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
