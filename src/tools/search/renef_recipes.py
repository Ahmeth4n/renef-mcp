from pathlib import Path
from typing import Dict

from src.app import mcp
from src.session import EXAMPLES_DIR, RECIPES_DIR, format_error, manager, to_json

_RECIPE_DESCRIPTIONS: Dict[str, str] = {
    "ssl_pinning_bypass": (
        "Bypass Java TrustManager/Conscrypt/OkHttp3 CertificatePinner, HostnameVerifier, "
        "and native BoringSSL SSL_CTX_set_custom_verify."
    ),
    "root_frida_detection_bypass": (
        "Disable su existence checks, Runtime.exec('su'), Build.TAGS, native strstr('frida'), "
        "and Frida port connect checks."
    ),
    "root_emulator_bypass": (
        "Modular RootDetection (hideSuBinaries, hidePackages, forceBooleanArgs) and "
        "EmulatorDetection (spoofBuildProps, spoofSystemProperties) namespaces."
    ),
    "taint_filter": (
        "Hook libc string/file functions (strstr, strcmp, openat, access, stat, fopen) "
        "against a verified anti-tamper wordlist with ABI-correct neutralization."
    ),
    "engine_capture": (
        "Catch runtime-decrypted native engines (e.g., DexProtector) by diffing anonymous "
        "executable mmap ranges on dlopen and dumping via File.write + send()."
    ),
    "java_reflection_dump": (
        "Reflection helpers: dump_class_schema, dump_instance_fields, java_tostring, "
        "and a Method.invoke() recon hook."
    ),
}


def _resolve_script(name: str, category: str = "recipes") -> Path:
    """Safely resolve a bundled recipe or example Lua script by name."""
    clean = name.strip()
    if not clean or "/" in clean or "\\" in clean or ".." in clean:
        raise ValueError(f"Invalid script name: {name!r}")
    if not clean.endswith(".lua"):
        clean += ".lua"

    base = RECIPES_DIR if category == "recipes" else EXAMPLES_DIR
    candidate = (base / clean).resolve()
    if not str(candidate).startswith(str(base.resolve())):
        raise ValueError(f"Path escape denied: {name!r}")
    if not candidate.is_file():
        # Try searching the other directory as convenience
        other = EXAMPLES_DIR if category == "recipes" else RECIPES_DIR
        alt = (other / clean).resolve()
        if str(alt).startswith(str(other.resolve())) and alt.is_file():
            return alt
        raise FileNotFoundError(f"Script not found: {name!r}")
    return candidate


@mcp.tool()
async def renef_recipes(
    action: str = "list",
    name: str = "",
    category: str = "recipes",
    timeout: float = 30.0,
) -> str:
    """List, inspect, or run bundled Renef v0.4.0 pentest recipes and example Lua scripts.

    Recipes are templates (not universal drop-ins) — use `action="get"` to read and tailor
    their `CONFIG` table before running, or `action="run"` to execute directly in the target.

    Actions:
    - `list` (default): List bundled recipes and examples
    - `get`: Return the full Lua source of a recipe/example by `name`
    - `run`: Execute a bundled recipe/example directly in the active target session

    Args:
        action: "list", "get", or "run"
        name: Script name (with or without `.lua`, e.g., "ssl_pinning_bypass", "taint_filter")
        category: "recipes" (default) or "examples"
        timeout: Execution timeout in seconds for `action="run"` (default: 30.0)

    Returns:
        JSON list of scripts, Lua source text, or execution result
    """
    try:
        act = action.strip().lower()
        cat = category.strip().lower()
        if act not in ("list", "get", "run"):
            return "ERROR: action must be 'list', 'get', or 'run'"
        if cat not in ("recipes", "examples"):
            return "ERROR: category must be 'recipes' or 'examples'"

        if act == "list":
            recipes = []
            if RECIPES_DIR.is_dir():
                for f in sorted(RECIPES_DIR.glob("*.lua")):
                    stem = f.stem
                    recipes.append(
                        {
                            "name": stem,
                            "file": f.name,
                            "uri": f"renef://recipes/{stem}",
                            "description": _RECIPE_DESCRIPTIONS.get(stem, ""),
                        }
                    )
            examples = []
            if EXAMPLES_DIR.is_dir():
                examples = [f.stem for f in sorted(EXAMPLES_DIR.glob("*.lua"))]

            return to_json(
                {
                    "ok": True,
                    "recipes_count": len(recipes),
                    "recipes": recipes,
                    "examples_count": len(examples),
                    "examples": examples,
                }
            )

        if not name.strip():
            return f"ERROR: name is required for action='{act}'"

        script_path = _resolve_script(name, category=cat)
        source = script_path.read_text(encoding="utf-8")

        if act == "get":
            return source

        # act == "run"
        def _run():
            session = manager.require_session()
            return session.eval(source, timeout=timeout)

        res = await manager.call(_run)
        if res.ok:
            manager.mark_exec_completed()
        return to_json(
            {
                "ok": res.ok,
                "script": script_path.name,
                "output": res.output or "",
                "error": res.error,
                "hint": "Call `renef_events` to collect hook output and `send()` events.",
            }
        )
    except Exception as exc:
        return format_error(exc)
