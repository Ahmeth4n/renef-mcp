try:
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as _MCPServer

_SERVER_INSTRUCTIONS = (
    "Renef v0.4.0 MCP Server — Dynamic instrumentation toolkit for Android ARM64 (Lua 5.4). "
    "IMPORTANT: Renef is NOT Frida. Never use Frida JS syntax (Java.perform, Interceptor.attach, "
    "Module.findExportByName with Frida callbacks). Read the `renef://api-reference` resource "
    "for the exact Renef v0.4.0 Lua API, and `renef://recipes` or `renef_recipes` for ready-to-run "
    "pentest scripts. Hook and syscall output is delivered on a separate event channel — call "
    "`renef_events` to collect hook output and structured `send()` events."
)

mcp = _MCPServer("renef", instructions=_SERVER_INSTRUCTIONS)
