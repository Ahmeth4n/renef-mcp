-- Strace Example: Custom filtering with Lua callback
-- Only logs openat calls that access specific paths
-- Usage: renef> l scripts/examples/strace_custom.lua -w

print("=== Custom Strace Filter ===")
print("Filtering openat calls for /data/ paths only")

Syscall.trace("openat", {
    onCall = function(info)
        local formatted = info.formatted
        -- Only print if path contains "/data/"
        if formatted and formatted:find("/data/") then
            print(CYAN .. formatted .. RESET)
        end
    end
})

print("")
print("Watching openat for /data/ paths...")
print("Run 'exec Syscall.stop()' to stop.")
