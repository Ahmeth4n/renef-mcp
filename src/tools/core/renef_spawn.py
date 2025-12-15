from src.app import mcp
from src import process as proc_module


@mcp.tool()
async def renef_spawn(package_name: str, hook_type: str = "") -> str:
    """
    Spawns a new process and injects the renef payload.

    Args:
        package_name: The package name of the app to spawn (e.g., com.example.app)
        hook_type: Hooking mechanism - 'pltgot' for PLT/GOT hooking, empty for default trampoline

    Returns:
        Spawn result (OK <pid> on success)
    """
    await proc_module.ensure_started()

    if hook_type:
        cmd = f"spawn {package_name} --hook={hook_type}\n"
    else:
        cmd = f"spawn {package_name}\n"

    proc_module.process.stdin.write(cmd.encode())
    await proc_module.process.stdin.drain()

    result = await proc_module.read_until_prompt()

    # Parse PID from "OK <pid>" response and store it
    # Example: "spawn com.example.app\nOK 12345"
    for line in result.split('\n'):
        line = line.strip()
        if line.startswith("OK "):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                proc_module.current_target_pid = int(parts[1])
                proc_module.current_target_package = package_name
                break

    return result
