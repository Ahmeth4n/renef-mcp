import asyncio
import os
import re
import platform
import sys

# Global process - stays open throughout the session
process: asyncio.subprocess.Process = None

# Track current target (PID or package name)
current_target_pid: int = None
current_target_package: str = None

# Get the script directory
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Detect platform and set correct renef binary path
def get_renef_binary_path():
    """Detect platform and return correct renef binary path"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":  # macOS
        if machine == "arm64":
            return os.path.join(SCRIPT_DIR, "bin", "macos-arm64", "renef")
        else:  # x86_64
            return os.path.join(SCRIPT_DIR, "bin", "macos-x64", "renef")
    elif system == "linux":
        return os.path.join(SCRIPT_DIR, "bin", "linux", "renef")
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")

RENEF_BINARY = get_renef_binary_path()

# Extended ANSI escape pattern (CSI + OSC sequences)
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07')


async def ensure_started():
    """Start the CLI (if not already started)"""
    global process
    if process is None or process.returncode is not None:
        # Ensure binary is executable
        if not os.path.exists(RENEF_BINARY):
            raise FileNotFoundError(f"Renef binary not found at: {RENEF_BINARY}")

        os.chmod(RENEF_BINARY, 0o755)

        process = await asyncio.create_subprocess_exec(
            RENEF_BINARY,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        # Skip initial prompt
        await read_until_prompt()


async def read_until_prompt(timeout: float = 30.0) -> str:
    """Read until prompt appears - PRESERVES RAW OUTPUT"""
    import time
    buffer = b""
    start_time = time.time()
    prompt_found = False

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break

            remaining = min(0.5, timeout - elapsed)
            try:
                chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=remaining)
                if not chunk:
                    break
                buffer += chunk
                if b"renef> " in buffer:
                    prompt_found = True
                    break
            except asyncio.TimeoutError:
                if b"renef> " in buffer:
                    prompt_found = True
                    break
                continue
    except Exception:
        pass

    # Decode
    text = buffer.decode('utf-8', errors='replace')

    # Remove ANSI codes
    clean = ANSI_ESCAPE.sub('', text)

    # Remove ONLY prompt (preserve whitespace)
    clean = clean.replace("renef> ", "")

    # Remove ONLY trailing newline if exists (not .strip()!)
    if clean.endswith('\n'):
        clean = clean[:-1]

    # Timeout indicator ONLY for real timeouts (no data received)
    if not prompt_found and not buffer:
        return "Timeout waiting for response"

    return clean
