"""Session & transport manager backed by the vendored Renef v0.4.0 pure-Python client.

Replaces the legacy CLI subprocess + prompt-scraping layer with direct framed
TCP communication to ``renef_server`` (127.0.0.1:1907 by default).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from src.renef_client.client import Client, Session, _STATUS_LINES, _is_rpc_reply, u64
from src.renef_client.errors import (
    CommandError,
    HookInstallError,
    LuaError,
    RenefConnectionError,
    RenefError,
    RenefTimeoutError,
    SessionClosedError,
)
from src.renef_client.lua import quote as lua_quote, to_lua
from src.renef_client.transport import DEFAULT_HOST, DEFAULT_PORT

T = TypeVar("T")

# Repository / package paths
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = PACKAGE_ROOT / "bin"
ANDROID_BIN_DIR = BIN_DIR / "android"
SCRIPTS_DIR = BIN_DIR / "scripts"
RECIPES_DIR = SCRIPTS_DIR / "recipes"
EXAMPLES_DIR = SCRIPTS_DIR / "examples"
TECHNIQUES_DIR = Path(__file__).resolve().parent / "techniques"

# On-device paths (Renef v0.4.0)
DEVICE_SERVER_PATH = "/data/local/tmp/renef_server"
DEVICE_AGENT_PATH = "/data/local/tmp/libagent.so"
DEVICE_LOG_PATH = "/data/local/tmp/renef.log"
DEVICE_DEFAULT_SOCKET = "localabstract:com.android.internal.os.RuntimeInit"

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


class McpSession(Session):
    """Session subclass that separates hook/trace output from command replies."""

    def __init__(self, client: "McpClient", pid: int):
        super().__init__(client, pid)
        self._hook_output: deque[str] = deque(maxlen=4000)

    def _append_hook_output(self, text: str) -> None:
        if not text:
            return
        lines = [
            ln
            for ln in text.split("\n")
            if ln and ln not in _STATUS_LINES and not _is_rpc_reply(ln)
        ]
        if lines:
            with self._state_lock:
                self._hook_output.extend(lines)

    def _fetch_pending_events(self, max_rounds: int = 8) -> None:
        """Drain buffered hook/trace output reported via ``ev=<n>`` markers."""
        for _ in range(max_rounds):
            raw = self._conn.request("events 0", timeout=15.0)
            text = self._process_output(raw)
            self._append_hook_output(text)
            if not self._conn.pending_events:
                break

    def poll_all(self, wait_ms: int = 0) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Poll ``events <wait_ms>`` and return ``(structured_events, output_lines)``."""
        if self._closed:
            raise SessionClosedError("Session is closed")
        clamped = max(0, min(int(wait_ms), 30000))
        raw = self._conn.request(
            f"events {clamped}",
            timeout=(clamped / 1000.0) + 10.0,
        )
        text = self._process_output(raw)
        self._append_hook_output(text)
        structured = self.events()
        with self._state_lock:
            output = list(self._hook_output)
            self._hook_output.clear()
        return structured, output

    def pending_counts(self) -> Tuple[int, int]:
        """Return ``(queued_structured_events, queued_output_lines)``."""
        with self._state_lock:
            return len(self._events), len(self._hook_output)

    def unhook_any(self, hook_id: str) -> str:
        """Remove native hook (``0``), Java hook (``j0``), or ``all``."""
        target = str(hook_id).strip()
        if not target or target.lower() == "all":
            out = self.command("unhook all")
            for hook in self._hooks.values():
                hook.removed = True
            self._hooks.clear()
            return out.strip() or "Removed all hooks"
        if not re.fullmatch(r"j?\d+", target):
            raise ValueError(
                f"Invalid hook_id {hook_id!r}. Must be 'all', a native integer ID (e.g. '0'), "
                "or a Java hook ID (e.g. 'j0')."
            )
        out = self.command(f"unhook {target}")
        if "ERROR:" in out:
            raise RenefError(out.strip())
        return out.strip()


class McpClient(Client):
    """Client subclass supporting v0.4.0 spawn-gate options and package-name attach."""

    session_class = McpSession

    def spawn_app(
        self,
        package: str,
        pause: bool = False,
        hold: bool = True,
        timeout: float = 30.0,
    ) -> McpSession:
        flags = ""
        if pause:
            flags += " --pause"
            if hold:
                flags += " --hold"
        command = f"spawn {package}{flags}"
        first = self._start(command, timeout, f"spawn {package}")
        try:
            pid = int(first.split()[1])
        except (IndexError, ValueError):
            raise CommandError(f"Unexpected reply to spawn: {first!r}") from None
        self._session = self.session_class(self, pid)
        return self._session  # type: ignore[return-value]

    def attach_target(self, target: Union[int, str], timeout: float = 30.0) -> McpSession:
        target_str = str(target).strip()
        if not target_str:
            raise CommandError("Target PID or package name is required")
        self._start(f"attach {target_str}", timeout, f"attach {target_str}")
        pid = int(target_str) if target_str.isdigit() else 0
        session = self.session_class(self, pid)
        self._session = session
        if pid == 0:
            try:
                resolved = session.OS.getpid()
                if isinstance(resolved, int) and resolved > 0:
                    session._pid = resolved
            except RenefError:
                pass
        return session  # type: ignore[return-value]


class SessionManager:
    """Process-wide manager for the Renef TCP client and active target session."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.host: str = os.environ.get("RENEF_HOST", DEFAULT_HOST)
        self.port: int = int(os.environ.get("RENEF_PORT", str(DEFAULT_PORT)))
        self._client: Optional[McpClient] = None
        self._session: Optional[McpSession] = None
        self.current_target_pid: Optional[int] = None
        self.current_target_package: Optional[str] = None
        self.is_paused: bool = False
        self.pause_hold: bool = False

    def configure(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Update target host/port and reset any existing connection."""
        with self._lock:
            self.reset_session()
            if host is not None:
                self.host = host
            if port is not None:
                self.port = int(port)

    def get_client(self, connect_timeout: float = 5.0) -> McpClient:
        with self._lock:
            if self._client is None or (
                self._client._conn_obj is not None and self._client._conn_obj.closed
            ):
                self._client = McpClient(self.host, self.port, connect_timeout=connect_timeout)
            _ = self._client._conn  # ensure connected
            return self._client

    def get_session(self) -> Optional[McpSession]:
        with self._lock:
            if self._session is not None and not self._session._closed:
                return self._session
            return None

    def require_session(self) -> McpSession:
        session = self.get_session()
        if session is None:
            raise RenefError(
                "No active target session. Call `renef_spawn` or `renef_attach` first."
            )
        return session

    def set_session(
        self,
        session: McpSession,
        package: Optional[str] = None,
        paused: bool = False,
        hold: bool = False,
    ) -> None:
        with self._lock:
            self._session = session
            self.current_target_pid = session.pid if session.pid > 0 else None
            self.current_target_package = package
            self.is_paused = paused
            self.pause_hold = paused and hold

    def mark_exec_completed(self) -> None:
        """Clear paused flag after exec/load when spawned with --pause without --hold."""
        with self._lock:
            if self.is_paused and not self.pause_hold:
                self.is_paused = False

    def reset_session(self) -> None:
        with self._lock:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None
            self._session = None
            self.current_target_pid = None
            self.current_target_package = None
            self.is_paused = False
            self.pause_hold = False

    async def call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a blocking Renef client call on a worker thread."""
        return await asyncio.to_thread(fn, *args, **kwargs)


# Global singleton used by all MCP tools
manager = SessionManager()


# ---------------------------------------------------------------------------
# Shared parsing & formatting helpers
# ---------------------------------------------------------------------------


def parse_address(value: Union[int, str], hex_default: bool = False) -> int:
    """Parse an integer address/offset from int or string (``0x1234`` / ``1234``)."""
    if isinstance(value, bool):
        raise ValueError(f"Invalid address: {value!r}")
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if not s:
        raise ValueError("Address cannot be empty")
    if s.lower().startswith("0x"):
        return int(s, 16)
    if hex_default:
        return int(s, 16)
    if s.isdigit():
        return int(s, 10)
    if _HEX_RE.match(s):
        return int(s, 16)
    raise ValueError(f"Invalid address/offset: {value!r}")


def parse_target_offset_or_symbol(target: Union[int, str]) -> Union[int, str]:
    """Return an ``int`` offset if ``target`` looks like a hex/decimal offset, else symbol ``str``."""
    if isinstance(target, int):
        return target
    s = str(target).strip()
    if not s:
        raise ValueError("Target offset or symbol name cannot be empty")
    if s.lower().startswith("0x"):
        return int(s, 16)
    if s.isdigit():
        return int(s, 10)
    return s


def parse_hex_bytes(hex_str: str) -> bytes:
    """Parse hex byte string (accepts spaces, ``0x``, ``\\x``, underscores)."""
    cleaned = (
        hex_str.strip()
        .replace(" ", "")
        .replace("_", "")
        .replace("\\x", "")
        .replace("0x", "")
        .replace("0X", "")
    )
    if not cleaned:
        raise ValueError("Hex bytes string cannot be empty")
    if len(cleaned) % 2 != 0:
        raise ValueError(f"Hex bytes string must have even length: {hex_str!r}")
    return bytes.fromhex(cleaned)


def normalize_java_class(class_name: str) -> str:
    """Normalize Java class name to JNI slash format (``com/example/Main``)."""
    s = class_name.strip()
    if s.startswith("L") and s.endswith(";") and ("/" in s or "." in s):
        s = s[1:-1]
    return s.replace(".", "/")


def format_error(err: Exception) -> str:
    """Format Renef / validation errors into concise, actionable MCP responses."""
    if isinstance(err, RenefConnectionError):
        return f"ERROR [connection]: {err}"
    if isinstance(err, RenefTimeoutError):
        partial = f"\nPartial output:\n{err.partial}" if getattr(err, "partial", "") else ""
        return f"ERROR [timeout]: {err}{partial}"
    if isinstance(err, LuaError):
        return f"ERROR [lua]: {err}"
    if isinstance(err, HookInstallError):
        return f"ERROR [hook]: {err}"
    if isinstance(err, SessionClosedError):
        return f"ERROR [session_closed]: {err}. Call `renef_spawn` or `renef_attach`."
    if isinstance(err, CommandError):
        return f"ERROR [command]: {err}"
    if isinstance(err, RenefError):
        return f"ERROR [renef]: {err}"
    return f"ERROR: {err}"


def to_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Shared ADB helper
# ---------------------------------------------------------------------------


async def run_adb(
    *args: str,
    timeout: float = 30.0,
    device_id: Optional[str] = None,
) -> Tuple[int, str]:
    """Run an ``adb`` command asynchronously with optional device selection and timeout."""
    dev = device_id or os.environ.get("RENEF_DEVICE_ID", "").strip()
    cmd = ["adb"]
    if dev and args and args[0] not in ("devices", "start-server", "kill-server"):
        cmd.extend(["-s", dev])
    cmd.extend(args)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode or 0, stdout.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return -1, f"ADB command timed out after {timeout}s: {' '.join(cmd)}"


__all__ = [
    "ANDROID_BIN_DIR",
    "BIN_DIR",
    "DEVICE_AGENT_PATH",
    "DEVICE_DEFAULT_SOCKET",
    "DEVICE_LOG_PATH",
    "DEVICE_SERVER_PATH",
    "EXAMPLES_DIR",
    "McpClient",
    "McpSession",
    "PACKAGE_ROOT",
    "RECIPES_DIR",
    "SCRIPTS_DIR",
    "SessionManager",
    "TECHNIQUES_DIR",
    "format_error",
    "lua_quote",
    "manager",
    "normalize_java_class",
    "parse_address",
    "parse_hex_bytes",
    "parse_target_offset_or_symbol",
    "run_adb",
    "to_json",
    "to_lua",
    "u64",
]
