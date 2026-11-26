"""MCP Resource providing the authoritative Renef v0.4.0 Lua API Reference."""

from src.app import mcp

RENEF_V040_API_REFERENCE = """# Renef v0.4.0 Lua API Reference (Android ARM64)

> **CRITICAL:** Renef is **NOT** Frida. Do **NOT** use Frida JavaScript syntax
> (`Java.perform`, `Interceptor.attach`, `Memory.readUtf8String`, `ptr(...)`, etc.).
> Renef scripts are **Lua 5.4** running inside `libagent.so` on Android ARM64.

---

## 1. Native Hooking (`hook`, `Interceptor`, `NativeFunction`)

### `hook(lib, offset, callbacks)`
- `lib`: library name string (e.g., `"libc.so"`, `"libnative.so"`). If not loaded yet, the hook is **deferred** and installed automatically when the library loads (pairs well with `renef_spawn(..., pause=True)`).
- `offset`: integer offset from library base (resolve via `Module.exports()` / `Module.findExportByName()`).
- `callbacks` table fields:
  - `onEnter = function(args) ... end` — `args[0]`..`args[7]` map to ARM64 registers `x0`..`x7`.
  - `onLeave = function(retval) ... return new_val end` — `retval` is `x0`; returning `nil` leaves `x0` unchanged, integer overrides `x0`, `0` = NULL.
  - `caller = "libapp.so"` (or `{"liba.so", "libb.so"}` or `"*"`) — selects **PLT/GOT** hooking for those callers instead of inline trampoline.
  - `async = true` — fire-and-forget observation-only `onEnter` off the hot path (native hooks only; cannot use `onLeave`).

### `Interceptor.replace(lib, offset, callback [, caller])` & `Interceptor.revert(lib, offset)`
- Replaces a native function: `callback(args)` runs **instead** of the original; its return value becomes `x0`.
- Call the original from inside `callback` via `NativeFunction(addr, ...)` (the reentrancy guard routes it to the original prologue).
- `Interceptor.revert(lib, offset)` restores original bytes / GOT entry.

### `NativeFunction(addr [, retType [, argTypes]])`
- Wraps a native ARM64 function address as a Lua callable.
- Up to 8 int/ptr args (`x0`-`x7`) + up to 8 float/double args (`d0`-`d7`).
- Supported types: `"int"`, `"long"`, `"pointer"` (default), `"bool"`, `"string"`, `"void"`, `"float"`, `"double"`.
- Example:
  ```lua
  local base = Module.find("libc.so")
  local exps = Module.findExportByName("libc.so", "strlen")
  local strlen = NativeFunction(base + exps[1].offset, "int", {"pointer"})
  print(strlen(Memory.allocStr("hello")))  -- 5
  ```

---

## 2. Java / ART Hooking & Reflection (`hook`, `Java`, `JNI`, `Jni`)

### `hook(class, method, signature, callbacks)`
- `class`: JNI slash format `"com/example/MyClass"` (NOT dots).
- `signature`: **Required** JNI signature, e.g. `"(Ljava/lang/String;)Z"`. (To hook all overloads of a method by name, use the `renef_hook_java` tool with empty `signature` or `hook_all_overloads(...)` from the `java_reflection_dump` recipe.)
- **Arg layout:**
  - Instance methods: `args[0]` = ArtMethod* (ignore), `args[1]` = `this`, `args[2]` = first Java param, `args[3]` = second param, ...
  - Static methods: `args[0]` = ArtMethod*, `args[1]` = first param (no `this`).
- **Bypassing void methods:** set `args.skip = true` in `onEnter` to skip the original method completely (essential for SSL pinning `checkServerTrusted`).
- **Modifying return values in `onLeave`:**
  - `nil` -> unchanged
  - `boolean` -> `true` / `false`
  - `integer` -> integer / raw ref
  - `JNI.string("text")` -> returns a new Java `String` (and `retval.value` reads original Java `String`, `retval.raw` is raw ref).
- Android 12+ uses the safe JNI twin engine (safe under exceptions & GC; listed as `[j0]` in `hooks` and removable via `unhook j0`).
- Wrap optional classes in `pcall(function() hook(...) end)`.

### `Java.*`
- `Java.use("android/os/Build")` -> class wrapper (`:call(method, sig, ...)`, `:new(sig, ...)`)
- Instance objects returned by `:new` / `:call` support `:call(method, sig, ...)` and `.raw`
- `Java.enumerateLoadedClasses()` -> array of class names from app's dex files
- `Java.methodInfo(class, method, sig)` -> `{method, flags, entry, jni, bound, native, static, hooked}`
- `Java.array(...)`, `Java.registerClass(...)`

### `JNI.*` (return/arg type tags) vs `Jni.*` (raw JNI helpers)
- `JNI.string(s)`, `JNI.int(n)`, `JNI.long(n)`, `JNI.boolean(b)`
- `Jni.newStringUTF(str)` -> pointer, `Jni.getStringUTF(ref)` -> string, `Jni.getStringLength(ref)` -> int, `Jni.deleteGlobalRef(ref)`

---

## 3. Memory API (`Memory`, `hexdump`)

- `Memory.read(addr, size)` -> raw bytes string
- `Memory.write(addr, bytes)` -> bool
- `Memory.patch(addr, bytes)` -> `ok, err` (auto `mprotect` + icache flush for RX/RO code)
- `Memory.alloc(size [, prot])` -> addr (`prot`: `"rw-"`, `"rwx"`, etc.)
- `Memory.allocStr(text)` -> addr of NUL-terminated string copy
- `Memory.free(addr [, size])`
- `Memory.protect(addr, size, prot)` -> `ok, err`
- `Memory.readU8/readU16/readU32/readU64(addr)` -> integer
- `Memory.writeU8/writeU16/writeU32/writeU64(addr, val)`
- `Memory.readStr(addr [, maxLen])` / `Memory.readString(addr [, maxLen])` -> string
- `Memory.search(pattern [, lib])` / `Memory.scan(...)` -> table of `{library, addr, offset, hex, ascii}` (supports plain strings and `"FD 7B ?? A9"` hex wildcards)
- `Memory.dump(results)` -> prints search results
- `Memory.hexdump(addr, len)` / global `hexdump(addr, len)` -> formatted hexdump string

---

## 4. Module, Disassembly, Process & Thread APIs

- `Module.find("libc.so")` -> base address integer or `nil`
- `Module.list()` -> string listing loaded modules
- `Module.exports("libc.so")` -> array of `{name, offset}` (`.dynsym`)
- `Module.symbols("libc.so")` -> array of `{name, offset}` (`.symtab`)
- `Module.findExportByName("libc.so", "pthread_*")` -> array of `{name, offset}` matching glob `*`/`?` (no wildcard = exact match)
- `Module.disassemble(addr, count)` -> array of `{address, size, mnemonic, op_str, is_branch, is_call, is_jump}` (max 1024; validates maps readability)
- `Process.enumerateRanges()` -> array of `{start, end, size, perms, path}` from `/proc/self/maps`
- `Process.enumerateThreads()` -> array of integer TIDs
- `Thread.id()` -> current TID
- `Thread.backtrace()` -> PAC-stripped call stack (auto-detects native hook & syscall callback context)

---

## 5. Syscall Tracing, File, OS, KCov & Events

- `Syscall.trace("openat", "read" [, {caller="libfoo.so", onCall=fn, onReturn=fn}])`
- `Syscall.trace({category="file"})` (`file`, `network`, `memory`, `process`, `ipc`)
- `Syscall.traceAll()`, `Syscall.untrace(...)`, `Syscall.stop()`, `Syscall.list([cat])`, `Syscall.active()`
- `File.read(path)`, `File.write(path, addr, size)`, `File.exists(path)`, `File.readlink(path)`, `File.fdpath(fd)`
- `OS.getpid()`, `OS.kill(pid, sig)`, `OS.tgkill(tgid, tid, sig)`, `OS.listdir(path)`
- `KCov.open([buf_size])` -> `cov:enable()`, `:disable()`, `:collect([max])`, `:count()`, `:edges()`, `:diff(old)`, `:reset()`, `:close()`
- `print(...)` / `console.log(msg)` -> human-readable output (from hook callbacks, arrives via `renef_events`)
- `send(table)` -> emits structured `[event] <JSON>` (collect via `renef_events`)
- ANSI colors: `RESET`, `RED`, `GREEN`, `YELLOW`, `BLUE`, `MAGENTA`, `CYAN`, `WHITE`
"""


@mcp.resource("renef://api-reference")
async def get_api_reference() -> str:
    """Authoritative Renef v0.4.0 Lua API reference for Android ARM64 instrumentation."""
    return RENEF_V040_API_REFERENCE
