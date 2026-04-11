-- Strace Example: File operations tracing
-- Usage: renef> l scripts/examples/strace_file.lua -w

print("=== File Syscall Tracing ===")

-- Trace file-related syscalls
Syscall.trace("openat", "read", "write", "close")

print("")
print("Interact with the app to see file operations.")
print("Run 'exec Syscall.stop()' to stop tracing.")
