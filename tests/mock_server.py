"""Offline mock renef_server implementing both framed and legacy wire protocols."""

from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class Reply:
    """A reply with an optional delay (models slow agent commands)."""

    def __init__(self, data: str | bytes, delay: float = 0.0):
        self.data = data.encode() if isinstance(data, str) else data
        self.delay = delay


class MockServer:
    def __init__(self, handler: Callable[[str], Any], framing: bool = True):
        self.handler = handler
        self.framing = framing
        self.commands: List[str] = []
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(4)
        self.port = self._sock.getsockname()[1]
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop = True
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self) -> "MockServer":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _serve(self) -> None:
        while not self._stop:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            threading.Thread(target=self._client, args=(conn,), daemon=True).start()

    def _run(self, command: str) -> bytes:
        self.commands.append(command)
        reply = self.handler(command)
        if isinstance(reply, Reply):
            if reply.delay:
                time.sleep(reply.delay)
            return reply.data
        if isinstance(reply, str):
            return reply.encode()
        return reply or b""

    def _client(self, conn: socket.socket) -> None:
        buf = b""
        try:
            while True:
                if self.framing and buf.startswith(b"@req "):
                    nl = buf.find(b"\n")
                    if nl >= 0:
                        rid, length = (int(x) for x in buf[5:nl].split())
                        if len(buf) >= nl + 1 + length:
                            payload = buf[nl + 1 : nl + 1 + length]
                            buf = buf[nl + 1 + length :]
                            command = payload.decode("utf-8", "surrogateescape").rstrip("\n")
                            reply = self._run(command)
                            pending = getattr(self.handler, "pending_count", lambda: 0)()
                            field = (b" ev=%d" % pending) if pending else b""
                            conn.sendall(reply + (b"\x1e@done %d%s\n" % (rid, field)))
                            continue
                elif buf.endswith(b"\n"):
                    command = buf.decode("utf-8", "surrogateescape").rstrip("\n")
                    buf = b""
                    if command.startswith("@req "):
                        conn.sendall(
                            b"ERROR: Unknown command. Type 'help' for available commands.\n"
                        )
                    else:
                        conn.sendall(self._run(command))
                    continue
                data = conn.recv(65536)
                if not data:
                    return
                buf += data
        except OSError:
            pass
        finally:
            conn.close()


class FakeRenefTarget:
    """Realistic v0.4.0 renef_server + agent handler for MCP tool tests."""

    def __init__(self) -> None:
        self.rpc: Dict[str, Any] = {}
        self.evals: List[str] = []
        self.hook_count: int = 0
        self.java_hooks: List[str] = []
        self.pending_events: List[Dict[str, Any]] = []
        self.pending_output_lines: List[str] = []
        self.announce_pending: bool = False
        self.defer_next_hook: bool = False
        self.paused_pid: Optional[int] = None
        self.verbose: bool = False

    def pending_count(self) -> int:
        if not self.announce_pending:
            return 0
        return len(self.pending_events) + len(self.pending_output_lines)

    def _default_rpc(self, command: str) -> Tuple[bool, Any]:
        # Match custom overrides first (longest key wins for specificity)
        for key in sorted(self.rpc.keys(), key=len, reverse=True):
            if key in command:
                return True, self.rpc[key]

        # Built-in realistic defaults for all v0.4.0 Lua APIs
        if "__renef_py.read(" in command:
            base_hex = "7f454c4602010100"
            try:
                size_str = command.split("__renef_py.read(", 1)[1].split(",", 1)[1].split(")", 1)[0].strip()
                n = int(size_str)
                return True, (base_hex * ((n // 8) + 1))[: n * 2]
            except (IndexError, ValueError):
                return True, base_hex
        if "__renef_py.write(" in command:
            return True, True
        if "__renef_py.readstr(" in command:
            return True, "hello_renef"
        if "Memory.patch(" in command:
            return True, True
        if "Memory.alloc(" in command:
            return True, 0x7000100000
        if "Memory.allocStr(" in command:
            return True, 0x7000200000
        if "Memory.free(" in command:
            return True, None
        if "Memory.protect(" in command:
            return True, True
        if "Memory.search(" in command:
            return True, [
                {
                    "addr": 0x7F10001234,
                    "offset": 0x1234,
                    "library": "libtarget.so",
                    "hex": "48 65 6c 6c 6f",
                    "ascii": "Hello",
                }
            ]
        if "hexdump(" in command:
            return True, "00000000  7f 45 4c 46 02 01 01 00  |.ELF....|"
        if "__renef_py.modules()" in command:
            return True, [
                {"name": "libc.so", "path": "/apex/com.android.runtime/lib64/bionic/libc.so", "base": 0x7A00000000, "size": 0x120000},
                {"name": "libflutter.so", "path": "/data/app/pkg/lib/arm64/libflutter.so", "base": 0x7B00000000, "size": 0x800000},
            ]
        if "Module.findExportByName(" in command:
            return True, [{"name": "open", "offset": 0x4400}, {"name": "openat", "offset": 0x4440}]
        if "Module.exports(" in command:
            return True, [{"name": "fopen", "offset": 0x1000}, {"name": "open", "offset": 0x4400}]
        if "Module.symbols(" in command:
            return True, [{"name": "__internal_fn", "offset": 0x800}, {"name": "open", "offset": 0x4400}]
        if "Module.disassemble(" in command:
            return True, [
                {"address": 0x7A00004400, "size": 4, "mnemonic": "stp", "op_str": "x29, x30, [sp, #-0x10]!", "is_branch": False, "is_call": False, "is_jump": False},
                {"address": 0x7A00004404, "size": 4, "mnemonic": "bl", "op_str": "#0x7a00005000", "is_branch": True, "is_call": True, "is_jump": False},
                {"address": 0x7A00004408, "size": 4, "mnemonic": "ret", "op_str": "", "is_branch": True, "is_call": False, "is_jump": False},
            ]
        if "Module.find(" in command and "libflutter.so" in command and "for k, libs in pairs" in command:
            return True, {"flutter": [{"name": "libflutter.so", "base": 0x7B00000000}]}
        if "Module.find(" in command:
            return True, 0x7A00000000
        if "Process.enumerateRanges()" in command:
            return True, [
                {"start": 0x7A00000000, "end": 0x7A00100000, "size": 0x100000, "perms": "r-xp", "path": "/apex/libc.so"},
                {"start": 0x7B00000000, "end": 0x7B00010000, "size": 0x10000, "perms": "rw-p", "path": ""},
            ]
        if "Process.enumerateThreads()" in command:
            return True, [4242, 4243, 4244]
        if "Thread.backtrace()" in command:
            return True, [
                {"index": 1, "pc": 0x7A00004404, "module": "libc.so", "offset": 0x4404, "base": 0x7A00000000, "path": "/apex/libc.so"}
            ]
        if "Thread.id()" in command:
            return True, 4242
        if "Java.enumerateLoadedClasses()" in command:
            return True, [
                "com.example.app.MainActivity",
                "com.example.app.net.PinningClient",
                "okhttp3.CertificatePinner",
            ]
        if "Java.methodInfo(" in command:
            return True, {
                "method": 0x7100001000,
                "flags": 0x0109,
                "entry": 0x7100002000,
                "jni": 0x7B00009999,
                "bound": True,
                "native": True,
                "static": True,
                "hooked": False,
            }
        if "__renef_py.objs[" in command and ".raw" in command:
            return True, 0x12C04080
        if "__renef_py.box(Java.use(" in command and ":new(" in command:
            return True, {"__py_obj": 1}
        if "__renef_py.box(Java.use(" in command and ":call(" in command:
            return True, 1700000000000
        if "__renef_py.box(__renef_py.objs[" in command:
            return True, True
        if "Jni.newStringUTF(" in command:
            return True, 0x12C08888
        if "Jni.getStringUTF(" in command:
            return True, "secret_java_str"
        if "Jni.getStringLength(" in command:
            return True, 15
        if "Syscall.list(" in command:
            return True, [
                {"name": "openat", "category": "file", "args": 4},
                {"name": "connect", "category": "network", "args": 3},
            ]
        if "Syscall.active()" in command:
            return True, [{"name": "openat", "category": "file", "hooks": 12}]
        if "File.read(" in command:
            return True, "<map><string name=\"token\">abc</string></map>"
        if "File.exists(" in command:
            return True, True
        if "File.readlink(" in command:
            return True, "/system/bin/app_process64"
        if "File.fdpath(" in command:
            return True, "/data/data/com.example.app/files/secret.db"
        if "File.write(" in command:
            return True, True
        if "OS.getpid()" in command:
            return True, 4242
        if "OS.listdir(" in command:
            return True, ["4242", "4243"]
        if "OS.kill(" in command or "OS.tgkill(" in command:
            return True, 0
        if "_kcov:count()" in command:
            return True, 42
        if "_kcov:collect(" in command:
            return True, [0xFFFFFFC0103A5E20, 0xFFFFFFC0103A5E48]
        if "_kcov:edges()" in command:
            return True, {"1024": 3, "2048": 1}
        if "getDeclaredMethods" in command and "pcall(hook" in command:
            self.java_hooks.append("com/example/App.getToken()Ljava/lang/String;")
            return True, {
                "installed": 2,
                "failed": 0,
                "signatures": ["()Ljava/lang/String;", "(I)Ljava/lang/String;"],
                "errors": [],
            }
        if "__renef_py.release(" in command:
            return True, None
        if "__renef_py.nf[" in command:
            return True, 5
        return False, None

    def __call__(self, command: str) -> Any:
        if command == "ping":
            return "pong\n"
        if command.startswith("spawn "):
            if "--pause" in command:
                self.paused_pid = 4242
            else:
                self.paused_pid = None
            return "OK 4242\n"
        if command.startswith("attach "):
            if "99999" in command:
                return "ERROR: Failed to attach\n"
            return "OK\n"
        if command == "resume":
            pid = self.paused_pid or 4242
            self.paused_pid = None
            return f"Resumed pid {pid}\n"
        if command.startswith("verbose "):
            self.verbose = command.endswith("on")
            return f"Verbose mode: {'ON' if self.verbose else 'OFF'}\n"
        if command.startswith("la"):
            apps = ["com.example.app", "com.android.settings", "com.test.flutter"]
            if "~" in command:
                flt = command.split("~", 1)[1]
                apps = [a for a in apps if flt in a]
            return "\n".join(apps) + f"\n\nTotal: {len(apps)} packages\n"
        if command == "hooks":
            lines = [f"Active hooks: {self.hook_count}"]
            for i in range(self.hook_count):
                lines.append(f"  [{i}] target=0x7a00004400 hits=3")
            if self.java_hooks:
                lines.append(f"Java hooks: {len(self.java_hooks)}")
                for i, desc in enumerate(self.java_hooks):
                    lines.append(f"  [j{i}] {desc} hits=1")
            return "\n".join(lines) + "\n"
        if command.startswith("unhook "):
            arg = command.split(None, 1)[1].strip()
            if arg == "all":
                total = self.hook_count + len(self.java_hooks)
                self.hook_count = 0
                self.java_hooks.clear()
                return f"Removed {total} hook(s)\n"
            if arg == "77":
                return "ERROR: Failed to remove hook\n"
            return f"Hook {arg} removed\n"
        if command.startswith("hookn "):
            self.hook_count += 1
            return f"Hook installed for {command[6:]}\n"
        if command.startswith("hookgen"):
            return 'hook("libc.so", 0x4400, {\n    onEnter = function(args) end\n})\n'
        if command.startswith("sec "):
            return ".text  0x1000  0x8000\n.rodata 0x9000 0x2000\n"
        if command.startswith("md "):
            if "-d" in command:
                return "0x7a00004400: stp x29, x30, [sp, #-0x10]!\n0x7a00004404: ret\n"
            return "0x7a00004400: 7f 45 4c 46 02 01 01 00  |.ELF....|\n"
        if command.startswith("memdump "):
            if "--maps" in command:
                return (
                    "MEMDUMP_MAPS pid=4242 starttime=123 comm=app\n"
                    "7a00000000-7a00100000 r-xp 00000000 00:00 0 /apex/libc.so\n"
                    "7b00000000-7b00200000 r-xp 00000000 00:00 0 /data/app/libapp.so\n"
                    "MEMDUMP_END\n"
                )
            return (
                "MEMDUMP_MANIFEST pid=4242\n"
                "SEG OK start=0x1000 len=4 hex=7f454c46\n"
                "SEG ERR start=0x1004 len=4 errno=5 msg=EIO\n"
                "MEMDUMP_SUMMARY total_requested=8 total_read=4 segments_ok=1 segments_err=1 hash=abc\n"
                "MEMDUMP_END\n"
            )
        if command.startswith("events"):
            chunks = []
            for ln in self.pending_output_lines:
                chunks.append(f"{ln}\n")
            for ev in self.pending_events:
                chunks.append(f"[event] {json.dumps(ev)}\n")
            self.pending_output_lines = []
            self.pending_events = []
            return "".join(chunks)
        if command.startswith("exec "):
            self.evals.append(command)
            eval_id = int(command.split("__py_eval = ")[1].split(",")[0])
            if "BOOM" in command:
                return (
                    f'[event] {{"__py_eval":{eval_id},"ok":false,"error":"eval:1: boom"}}\n'
                    "ERROR: Lua execution failed\n"
                )
            if "FAILHOOK" in command:
                return (
                    f'[event] {{"__py_eval":{eval_id},"ok":false,"error":"Failed to install native hook"}}\n'
                    "OK\n"
                )
            if "hook(" in command:
                if self.defer_next_hook:
                    self.defer_next_hook = False
                else:
                    # Distinguish Java hook (3-4 string args) vs native hook (lib, 0x...)
                    if "onEnter" in command and "0x" not in command.split("hook(", 1)[1][:40]:
                        self.java_hooks.append("com/example/App.check()V")
                    else:
                        self.hook_count += 1
            printed = ""
            if "PRINT_HELLO" in command:
                printed = "hello from lua\n"
            elif "Syscall.trace" in command:
                printed = "Tracing syscall(s)\n"
            elif "Syscall.stop" in command:
                printed = "Syscall tracing stopped\n"
            elif "Syscall.untrace" in command:
                printed = "Removed 1 trace(s)\n"
            elif "KCov.open" in command:
                printed = "KCov opened: 262144 entries\nok\n"
            return f'{printed}[event] {{"__py_eval":{eval_id},"ok":true}}\nOK\n'
        if command.startswith("rpc "):
            matched, value = self._default_rpc(command)
            if matched:
                if isinstance(value, Exception):
                    return (
                        f'{{"ok":false,"error":{json.dumps(str(value))},"__rpc_call":true}}\n'
                    )
                if isinstance(value, Reply):
                    return value
                return json.dumps({"ok": True, "value": value, "__rpc_call": True}) + "\n"
            return '{"ok":true,"value":null,"__rpc_call":true}\n'
        return "ERROR: Unknown command. Type 'help' for available commands.\n"
