from src.app import mcp
from src.session import format_error, lua_quote, manager, normalize_java_class, to_json


def _build_all_overloads_lua(cls: str, method: str, cb_table: str) -> str:
    """Discover every declared overload of `cls.method` via reflection and install `hook()` on each."""
    return f"""
(function()
    local Class_ = Java.use("java/lang/Class")
    local ReflectArray_ = Java.use("java/lang/reflect/Array")
    local dotted = string.gsub({lua_quote(cls)}, "/", ".")
    local ok, cls_obj = pcall(function()
        return Class_:call("forName", "(Ljava/lang/String;)Ljava/lang/Class;", dotted)
    end)
    if not ok or not cls_obj then
        local ok2, cls2 = pcall(function()
            local AT = Java.use("android/app/ActivityThread")
            local app = AT and AT:call("currentApplication", "()Landroid/app/Application;")
            if not app then return nil end
            local loader = app:call("getClassLoader", "()Ljava/lang/ClassLoader;")
            if not loader then return nil end
            return Class_:call("forName", "(Ljava/lang/String;ZLjava/lang/ClassLoader;)Ljava/lang/Class;", dotted, true, loader)
        end)
        cls_obj = (ok2 and cls2) or nil
    end
    if not cls_obj then
        error("class not resolved: " .. dotted, 0)
    end

    local PRIM = {{ int="I", boolean="Z", byte="B", char="C", short="S", long="J", float="F", double="D", ["void"]="V" }}
    local function to_jni(c)
        local n = c:call("getName", "()Ljava/lang/String;")
        if not n then return "Ljava/lang/Object;" end
        if n:sub(1, 1) == "[" then return (n:gsub("%.", "/")) end
        if PRIM[n] then return PRIM[n] end
        return "L" .. n:gsub("%.", "/") .. ";"
    end

    local methods = cls_obj:call("getDeclaredMethods", "()[Ljava/lang/reflect/Method;")
    local mlen = methods and ReflectArray_:call("getLength", "(Ljava/lang/Object;)I", methods) or 0
    local cbs = {cb_table}
    local installed, failed = 0, 0
    local hooked_sigs, errors = {{}}, {{}}

    for i = 0, mlen - 1 do
        local m = ReflectArray_:call("get", "(Ljava/lang/Object;I)Ljava/lang/Object;", methods, i)
        if m and m:call("getName", "()Ljava/lang/String;") == {lua_quote(method)} then
            local pts = m:call("getParameterTypes", "()[Ljava/lang/Class;")
            local plen = pts and ReflectArray_:call("getLength", "(Ljava/lang/Object;)I", pts) or 0
            local sig = "("
            for j = 0, plen - 1 do
                local pt = ReflectArray_:call("get", "(Ljava/lang/Object;I)Ljava/lang/Object;", pts, j)
                sig = sig .. to_jni(pt)
            end
            local rt = m:call("getReturnType", "()Ljava/lang/Class;")
            sig = sig .. ")" .. to_jni(rt)

            local hok, herr = pcall(hook, {lua_quote(cls)}, {lua_quote(method)}, sig, cbs)
            if hok then
                installed = installed + 1
                hooked_sigs[#hooked_sigs + 1] = sig
            else
                failed = failed + 1
                errors[#errors + 1] = sig .. ": " .. tostring(herr)
            end
        end
    end
    return {{ installed = installed, failed = failed, signatures = hooked_sigs, errors = errors }}
end)()
""".strip()


@mcp.tool()
async def renef_hook_java(
    class_name: str,
    method_name: str,
    signature: str = "",
    on_enter: str = "",
    on_leave: str = "",
    skip_original: bool = False,
    return_value: str = "",
) -> str:
    """Install a Java/ART method hook (Android 12+ safe JNI twin engine; fallback on older Android).

    Java hook argument layout in Lua callbacks:
    - Instance methods: `args[0]` = ArtMethod* (internal), `args[1]` = `this`, `args[2]` = arg1, ...
    - Static methods: `args[0]` = ArtMethod*, `args[1]` = arg1, ...
    - `skip_original=True` sets `args.skip = true` in onEnter (CRITICAL for bypassing void methods
      like SSL pinning checks without triggering exceptions).
    - `return_value` overrides the return value in onLeave: e.g. `"false"`, `"true"`, `"0"`, `"42"`,
      or `'JNI.string("HOOKED")'`.
    - When `signature` is omitted, discovers all declared overloads of `method_name` via Java
      reflection and installs the hook on each overload.
    - Java hooks appear in `renef_hooks_list()` as `[j0]`, `[j1]`, ... and can be removed with
      `renef_unhook("j0")` or `renef_unhook("all")`.

    Args:
        class_name: Class name (dots or slashes accepted, normalized to "com/example/Main")
        method_name: Java method name (e.g., "isRooted", "checkServerTrusted")
        signature: Optional JNI signature (e.g., "()Z", "(Ljava/lang/String;)Ljava/lang/String;").
                   Leave empty to discover and hook all declared overloads via reflection.
        on_enter: Optional Lua body for onEnter (`args` in scope)
        on_leave: Optional Lua body for onLeave (`retval` in scope)
        skip_original: If True, sets `args.skip = true` in onEnter to skip calling the original method
        return_value: Optional Lua expression returned from onLeave (e.g., "false", 'JNI.string("ok")')

    Returns:
        JSON status confirming installation
    """
    try:
        cls = normalize_java_class(class_name)
        method = method_name.strip()
        sig = signature.strip()
        if not cls or not method:
            return "ERROR: class_name and method_name are required"

        enter_parts = []
        if on_enter.strip():
            enter_parts.append(on_enter.strip())
        if skip_original:
            enter_parts.append("args.skip = true")

        leave_parts = []
        if on_leave.strip():
            leave_parts.append(on_leave.strip())
        if return_value.strip():
            leave_parts.append(f"return {return_value.strip()}")

        # If no custom behavior requested, install a type-safe default logger
        if not enter_parts and not leave_parts:
            tag = lua_quote(f"{cls}.{method}{sig}")
            enter_parts.append(
                f"local parts = {{}} "
                f"for i = 1, 6 do "
                f"  local v = args[i] "
                f"  if v ~= nil then "
                f"    parts[#parts + 1] = string.format('a%d=%s', i, type(v) == 'number' and string.format('0x%x', v) or tostring(v)) "
                f"  end "
                f"end "
                f'print("[java enter] " .. {tag} .. " " .. table.concat(parts, " "))'
            )
            leave_parts.append(
                f"local rv "
                f"if type(retval) == 'table' then "
                f"  rv = retval.value ~= nil and tostring(retval.value) or string.format('0x%x', retval.raw or 0) "
                f"elseif type(retval) == 'number' then "
                f"  rv = string.format('0x%x', retval) "
                f"else rv = tostring(retval) end "
                f'print("[java leave] " .. {tag} .. " -> " .. rv)'
            )

        cb_parts = []
        if enter_parts:
            cb_parts.append("onEnter = function(args)\n" + "\n".join(enter_parts) + "\nend")
        if leave_parts:
            cb_parts.append("onLeave = function(retval)\n" + "\n".join(leave_parts) + "\nend")
        cb_table = "{ " + ", ".join(cb_parts) + " }"

        if sig:
            lua_code = f"hook({lua_quote(cls)}, {lua_quote(method)}, {lua_quote(sig)}, {cb_table})"

            def _install_single():
                session = manager.require_session()
                res = session.eval(lua_code)
                if not res.ok:
                    raise RuntimeError(res.error or res.output or "Java hook failed")
                return res.output or ""

            output = await manager.call(_install_single)
            return to_json(
                {
                    "ok": True,
                    "class": cls,
                    "method": method,
                    "signature": sig,
                    "skip_original": skip_original,
                    "return_value": return_value or None,
                    "output": output,
                    "hint": "Call `renef_hooks_list` to view hook ID (`jN`) and `renef_events` for call logs.",
                }
            )

        # No signature: discover & hook all declared overloads via reflection
        overload_expr = _build_all_overloads_lua(cls, method, cb_table)

        def _install_overloads():
            session = manager.require_session()
            return session.rpc(overload_expr, timeout=60.0)

        summary = await manager.call(_install_overloads)
        if not isinstance(summary, dict):
            summary = {"installed": 0, "failed": 0, "signatures": [], "errors": []}
        installed = int(summary.get("installed", 0))
        failed = int(summary.get("failed", 0))
        return to_json(
            {
                "ok": installed > 0,
                "class": cls,
                "method": method,
                "signature": "(all overloads)",
                "installed": installed,
                "failed": failed,
                "signatures": summary.get("signatures", []),
                "errors": summary.get("errors", []),
                "hint": "Call `renef_hooks_list` to view hook IDs (`jN`) and `renef_events` for call logs.",
            }
        )
    except Exception as exc:
        return format_error(exc)
