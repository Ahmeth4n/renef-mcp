from src.app import mcp
from src.session import (
    format_error,
    lua_quote,
    manager,
    normalize_java_class,
    to_json,
    u64,
)


@mcp.tool()
async def renef_java_method_info(
    class_name: str,
    method_name: str,
    signature: str,
) -> str:
    """Inspect ART metadata for a Java method using `Java.methodInfo`.

    Returns the `ArtMethod*` pointer, access flags, quick entry point, JNI native function pointer
    (if native) and whether it is bound, plus `native`, `static`, and `hooked` booleans.

    Args:
        class_name: Java class name (dots or slashes accepted, e.g., "com/example/NativeBridge")
        method_name: Method name (e.g., "checkLicense")
        signature: JNI signature (e.g., "(Ljava/lang/String;)Z")

    Returns:
        JSON object with ART method details
    """
    try:
        cls = normalize_java_class(class_name)
        method = method_name.strip()
        sig = signature.strip()
        if not cls or not method or not sig:
            return "ERROR: class_name, method_name, and signature are all required"

        expr = (
            "(function() "
            f"local info, err = Java.methodInfo({lua_quote(cls)}, {lua_quote(method)}, {lua_quote(sig)}); "
            'if not info then error(tostring(err or "methodInfo failed"), 0) end; '
            "return info end)()"
        )

        def _info():
            session = manager.require_session()
            return session.rpc(expr)

        info = await manager.call(_info)
        if not isinstance(info, dict):
            return to_json({"ok": True, "info": info})

        method_ptr = u64(info.get("method", 0))
        entry_ptr = u64(info.get("entry", 0))
        flags = int(info.get("flags", 0))
        out = {
            "ok": True,
            "class": cls,
            "method": method,
            "signature": sig,
            "art_method": method_ptr,
            "art_method_hex": f"0x{method_ptr:x}",
            "flags": flags,
            "flags_hex": f"0x{flags:x}",
            "entry": entry_ptr,
            "entry_hex": f"0x{entry_ptr:x}",
            "native": bool(info.get("native")),
            "static": bool(info.get("static")),
            "hooked": bool(info.get("hooked")),
        }
        if "jni" in info and info["jni"] is not None:
            jni_ptr = u64(info["jni"])
            out["jni"] = jni_ptr
            out["jni_hex"] = f"0x{jni_ptr:x}"
        if "bound" in info:
            out["bound"] = bool(info["bound"])
        return to_json(out)
    except Exception as exc:
        return format_error(exc)
