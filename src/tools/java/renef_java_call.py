from typing import Any, List, Optional

from src.app import mcp
from src.renef_client.client import JavaObject
from src.session import format_error, manager, normalize_java_class, to_json


@mcp.tool()
async def renef_java_call(
    class_name: str = "",
    method_name: str = "",
    signature: str = "()V",
    args: Optional[List[Any]] = None,
    constructor: bool = False,
    instance_handle: int = 0,
    release: bool = False,
    timeout: float = 30.0,
) -> str:
    """Call a Java static method, construct an instance, or call/release a boxed JavaObject.

    Uses Renef v0.4.0's `Java.use(class):call(...)` / `:new(...)` and instance handles.

    Examples:
    - Static call: `class_name="java/lang/System"`, `method_name="currentTimeMillis"`, `signature="()J"`
    - Constructor: `class_name="java/io/File"`, `constructor=True`, `signature="(Ljava/lang/String;)V"`, `args=["/data/local/tmp"]`
    - Instance call: `instance_handle=1`, `method_name="exists"`, `signature="()Z"`
    - Release handle: `instance_handle=1`, `release=True`

    Args:
        class_name: Java class name (dots or slashes accepted; required unless `instance_handle > 0`)
        method_name: Method name (required unless `constructor=True` or `release=True`)
        signature: JNI method/constructor signature (e.g., "()Ljava/lang/String;", "(Ljava/lang/String;)V")
        args: Optional argument list (strings, ints, bools, floats, or None)
        constructor: If True, constructs a new instance via `:new(signature, ...)`
        instance_handle: Existing JavaObject handle returned by a previous call/constructor
        release: If True with `instance_handle > 0`, releases the target-side JNI reference
        timeout: RPC timeout in seconds (default: 30.0)

    Returns:
        JSON object with the return value (or `{handle, raw_hex}` for returned Java objects)
    """
    try:
        if release:
            if instance_handle <= 0:
                return "ERROR: instance_handle > 0 is required when release=True"

            def _release():
                session = manager.require_session()
                JavaObject(session, int(instance_handle)).release()

            await manager.call(_release)
            return to_json({"ok": True, "released_handle": int(instance_handle)})

        call_args = list(args or [])
        sig = signature.strip()
        if not sig:
            return "ERROR: signature is required (e.g., '()V', '()Ljava/lang/String;')"

        def _invoke():
            session = manager.require_session()
            if instance_handle > 0:
                if not method_name.strip():
                    raise ValueError("method_name is required when calling on an instance_handle")
                obj = JavaObject(session, int(instance_handle))
                return obj.call(method_name.strip(), sig, *call_args, timeout=timeout)

            cls_norm = normalize_java_class(class_name)
            if not cls_norm:
                raise ValueError("class_name is required when instance_handle is not provided")
            wrapper = session.Java.use(cls_norm)
            if constructor:
                return wrapper.new(sig, *call_args, timeout=timeout)
            if not method_name.strip():
                raise ValueError("method_name is required for static Java method calls")
            return wrapper.call(method_name.strip(), sig, *call_args, timeout=timeout)

        res = await manager.call(_invoke)
        if isinstance(res, JavaObject):
            raw_ptr = await manager.call(lambda: res.raw)
            return to_json(
                {
                    "ok": True,
                    "type": "java_object",
                    "handle": res.handle,
                    "raw": raw_ptr,
                    "raw_hex": f"0x{raw_ptr:x}",
                }
            )
        return to_json({"ok": True, "value": res})
    except Exception as exc:
        return format_error(exc)
