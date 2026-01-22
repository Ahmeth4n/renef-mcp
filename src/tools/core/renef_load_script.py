from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_load_script(script_paths: str) -> str:
    """
    Loads and executes Lua script(s) in the target process.

    Args:
        script_paths: Path(s) to Lua script file(s), space-separated for multiple files
                      (e.g., 'hook.lua' or 'init.lua hooks.lua utils.lua')

    Returns:
        Script execution result
    """
    await proc_module.ensure_started()

    cmd = f"l {script_paths}\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    return await proc_module.read_until_prompt()
