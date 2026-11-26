"""MCP Prompts providing Renef v0.4.0 scripting instructions."""

from src.app import mcp
from src.resources.api_reference import RENEF_V040_API_REFERENCE


@mcp.prompt()
async def renef_lua_guide(task: str = "") -> str:
    """Return a concise Renef v0.4.0 Lua scripting guide (anti-Frida guardrails + API reference).

    Args:
        task: Optional description of the instrumentation task you are planning
    """
    header = (
        "You are assisting with dynamic instrumentation of an Android ARM64 target using "
        "Renef v0.4.0 (Lua 5.4). Follow the Renef API strictly — NEVER write Frida JS syntax.\n"
        "Workflow tips:\n"
        "1. Prefer passive `renef_memdump_passive` or default signal-based `renef_spawn`/`renef_attach` "
        "against anti-debug targets; use `pause=True` only when early spawn-gate hooks are needed.\n"
        "2. Verify loaded modules, exports (`renef_module_exports`), and Java classes (`renef_java_classes`) "
        "before writing hooks — never guess offsets or class names.\n"
        "3. Hook/trace output arrives on a separate event channel — always call `renef_events` to collect it.\n"
        "4. Check `renef_recipes` for official v0.4.0 templates (SSL pinning, root/emulator bypass, "
        "taint filter, DexProtector engine capture, Java reflection dump).\n\n"
    )
    if task.strip():
        header += f"Current task: {task.strip()}\n\n"
    return header + RENEF_V040_API_REFERENCE
