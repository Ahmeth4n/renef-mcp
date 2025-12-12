from src.app import mcp
from src import process as proc_module
from src.tools.core.renef_zero_copy_multiline_exec import zero_copy_multiline_exec


@mcp.tool()
async def renef_detect_framework() -> str:
    """
    Detects the application framework by analyzing loaded libraries.

    Identifies common frameworks such as:
    - Flutter (libflutter.so, libapp.so)
    - React Native (libhermes.so, libreactnativejni.so)
    - Unity (libunity.so, libil2cpp.so)
    - Xamarin (libmono-android.so, libmono.so)
    - Native (no framework detected)

    Returns:
        Detected framework information with library details
    """
    await proc_module.ensure_started()

    # Lua code to detect frameworks
    lua_code = """
local frameworks = {
    flutter = {"libflutter.so", "libapp.so"},
    react_native = {"libhermes.so", "libreactnativejni.so", "libreactnative.so"},
    unity = {"libunity.so", "libil2cpp.so"},
    xamarin = {"libmono-android.so", "libmono.so", "libmonodroid.so"},
    cordova = {"libcordova.so"},
    ionic = {"libcordova.so"},
    native_script = {"libnativescript.so"}
}

local detected = {}

for framework, libs in pairs(frameworks) do
    for _, lib_pattern in ipairs(libs) do
        local lib_base = Module.find(lib_pattern)
        if lib_base then
            if not detected[framework] then
                detected[framework] = {}
            end
            table.insert(detected[framework], {name = lib_pattern, base = lib_base})
        end
    end
end

if next(detected) == nil then
    print("Framework: Native")
    print("No common framework libraries detected")
else
    for framework, libs in pairs(detected) do
        print("Framework: " .. framework)
        for _, lib in ipairs(libs) do
            print("  - " .. lib.name .. " @ " .. lib.base)
        end
    end
end
"""

    return await zero_copy_multiline_exec(lua_code)
