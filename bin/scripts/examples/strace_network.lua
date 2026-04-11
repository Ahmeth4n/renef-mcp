-- Strace Example: Network operations tracing with custom callback
-- Usage: renef> l scripts/examples/strace_network.lua -w

print("=== Network Syscall Tracing ===")

-- Trace network category with custom callback to filter output
Syscall.trace("connect", "sendto", "recvfrom", "socket", {
    onCall = function(info)
        -- Only print, formatted output is already available
        print(info.formatted)
    end,
    onReturn = function(info)
        if info.retval < 0 then
            print("  -> ERROR: " .. (info.errno_str or "unknown"))
        end
    end
})

print("")
print("Watching network syscalls...")
print("Run 'exec Syscall.stop()' to stop tracing.")
