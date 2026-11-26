from src.app import mcp
from src.session import format_error, manager, to_json, u64

_FRAMEWORK_LIBS = {
    "flutter": ["libflutter.so", "libapp.so"],
    "react_native": ["libhermes.so", "libreactnativejni.so", "libreactnative.so"],
    "unity": ["libunity.so", "libil2cpp.so"],
    "xamarin": ["libmono-android.so", "libmono.so", "libmonodroid.so"],
    "cordova_ionic": ["libcordova.so"],
    "nativescript": ["libnativescript.so"],
}


@mcp.tool()
async def renef_detect_framework() -> str:
    """Detect the Android app's framework by checking loaded native libraries.

    Identifies Flutter, React Native, Unity, Xamarin, Cordova/Ionic, NativeScript, or
    Android Native, and recommends the matching `techniques://ssl_pinning/{platform}` URI.

    Returns:
        JSON object with detected frameworks, matched libraries + hex base addresses, and resource hints
    """
    try:
        lua_expr = (
            "(function() "
            "local fw = {"
            'flutter={"libflutter.so","libapp.so"}, '
            'react_native={"libhermes.so","libreactnativejni.so","libreactnative.so"}, '
            'unity={"libunity.so","libil2cpp.so"}, '
            'xamarin={"libmono-android.so","libmono.so","libmonodroid.so"}, '
            'cordova_ionic={"libcordova.so"}, '
            'nativescript={"libnativescript.so"}'
            "} "
            "local res = {} "
            "for k, libs in pairs(fw) do "
            "  local hits = {} "
            "  for _, lib in ipairs(libs) do "
            "    local b = Module.find(lib) "
            "    if b then hits[#hits+1] = {name=lib, base=b} end "
            "  end "
            "  if #hits > 0 then res[k] = hits end "
            "end "
            "return res end)()"
        )

        def _detect():
            session = manager.require_session()
            return session.rpc(lua_expr) or {}

        raw = await manager.call(_detect)
        detected = {}
        if isinstance(raw, dict):
            for fw_name, libs in raw.items():
                if isinstance(libs, list):
                    detected[fw_name] = [
                        {
                            "name": entry.get("name", ""),
                            "base": u64(entry.get("base", 0)),
                            "base_hex": f"0x{u64(entry.get('base', 0)):x}",
                        }
                        for entry in libs
                        if isinstance(entry, dict)
                    ]

        primary = next(iter(detected.keys()), "android_native")
        ssl_resource = (
            f"techniques://ssl_pinning/{primary}"
            if primary in ("flutter", "react_native", "unity", "xamarin", "cordova_ionic", "android_native")
            else "techniques://ssl_pinning/android_native"
        )
        return to_json(
            {
                "ok": True,
                "primary_framework": primary,
                "detected": detected,
                "ssl_pinning_resource": ssl_resource,
            }
        )
    except Exception as exc:
        return format_error(exc)
