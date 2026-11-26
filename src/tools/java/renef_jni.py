from src.app import mcp
from src.session import (
    format_error,
    lua_quote,
    manager,
    parse_address,
    to_json,
    to_lua,
    u64,
)


@mcp.tool()
async def renef_jni(
    action: str,
    value: str = "",
    ref: str = "",
) -> str:
    """Raw JNI string & reference helpers (`Jni.*` API — distinct from `JNI.*` return tags).

    Actions:
    - `new_string`: Create a Java String from UTF-8 text -> `Jni.newStringUTF(value)` (returns ref pointer)
    - `get_string`: Read UTF-8 text from a `jstring` or raw ART `String*` pointer -> `Jni.getStringUTF(ref)`
    - `string_length`: Get UTF-16 character length of a `jstring` / ART `String*` -> `Jni.getStringLength(ref)`
    - `delete_ref`: Delete a JNI global reference -> `Jni.deleteGlobalRef(ref)`

    Args:
        action: "new_string", "get_string", "string_length", or "delete_ref"
        value: UTF-8 string value (required for "new_string")
        ref: JNI reference / ART String* address (required for "get_string", "string_length", "delete_ref")

    Returns:
        JSON object with JNI operation result
    """
    try:
        act = action.strip().lower()
        if act not in ("new_string", "get_string", "string_length", "delete_ref"):
            return "ERROR: action must be 'new_string', 'get_string', 'string_length', or 'delete_ref'"

        if act == "new_string":
            def _new():
                session = manager.require_session()
                return u64(session.rpc(f"Jni.newStringUTF({lua_quote(value)})"))

            ptr = await manager.call(_new)
            return to_json({"ok": True, "action": "new_string", "ref": ptr, "ref_hex": f"0x{ptr:x}"})

        addr = parse_address(ref)
        if act == "get_string":
            def _get():
                session = manager.require_session()
                return session.rpc(f"Jni.getStringUTF({to_lua(addr)})")

            text = await manager.call(_get)
            return to_json({"ok": True, "action": "get_string", "ref_hex": f"0x{addr:x}", "value": text})

        if act == "string_length":
            def _len():
                session = manager.require_session()
                return session.rpc(f"Jni.getStringLength({to_lua(addr)})")

            length = await manager.call(_len)
            return to_json({"ok": True, "action": "string_length", "ref_hex": f"0x{addr:x}", "length": length})

        # delete_ref
        def _del():
            session = manager.require_session()
            res = session.eval(f"Jni.deleteGlobalRef({to_lua(addr)})")
            if not res.ok:
                raise RuntimeError(res.error or "deleteGlobalRef failed")

        await manager.call(_del)
        return to_json({"ok": True, "action": "delete_ref", "ref_hex": f"0x{addr:x}"})
    except Exception as exc:
        return format_error(exc)
