from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_attach(pid: int, hook_type: str = "") -> str:
    """
    Attaches to a running process by PID and injects the renef payload.

    Args:
        pid: The process ID to attach to
        hook_type: Hooking mechanism - 'pltgot' for PLT/GOT hooking, empty for default trampoline

    Returns:
        Attach result (OK on success)
    """
    await proc_module.ensure_started()

    if hook_type:
        cmd = f"attach {pid} --hook={hook_type}\n"
    else:
        cmd = f"attach {pid}\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    # Use longer timeout for attach (injection can take time)
    result = await proc_module.read_until_prompt(timeout=60.0)

    # Store target PID on successful attach
    if "ok" in result.lower() and "error" not in result.lower():
        proc_module.current_target_pid = pid

    return result
