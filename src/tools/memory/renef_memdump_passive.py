import hashlib
from pathlib import Path

from src.app import mcp
from src.session import format_error, manager, parse_address, to_json


@mcp.tool()
async def renef_memdump_passive(
    pid: int,
    mode: str = "maps",
    start_addr: str = "",
    end_addr: str = "",
    filter: str = "",
    output_path: str = "",
) -> str:
    """Injection-free, ptrace-free passive memory read via renef_server (`/proc/<pid>/maps` & `/proc/<pid>/mem`).

    Does NOT spawn, attach, inject `libagent.so`, or call `ptrace`. Ideal for inspecting
    anti-tamper / anti-debug targets before deciding whether to inject.

    Modes:
    - `maps` (default): Lists memory mappings from `/proc/<pid>/maps` (optional substring `filter`).
    - `dump`: Reads raw bytes in `[start_addr, end_addr)` directly from `/proc/<pid>/mem`.
      If `output_path` is provided, writes the binary dump to that host file.

    Args:
        pid: Target process PID on the Android device
        mode: "maps" (default) or "dump"
        start_addr: Start hex address (required for mode="dump", e.g., "0x7f10000000")
        end_addr: End hex address (required for mode="dump", e.g., "0x7f10004000")
        filter: Optional substring filter for `mode="maps"` lines (e.g., "libapp.so", "r-xp")
        output_path: Optional host file path to write the maps text or raw binary dump

    Returns:
        JSON object with maps lines or dump metadata/hex preview
    """
    try:
        if pid <= 0:
            return "ERROR: pid must be a positive integer"
        mode_norm = mode.strip().lower()
        if mode_norm not in ("maps", "dump"):
            return "ERROR: mode must be 'maps' or 'dump'"

        if mode_norm == "maps":
            def _maps():
                client = manager.get_client()
                return client.memdump_maps(int(pid))

            raw_maps = await manager.call(_maps)
            lines = [ln for ln in raw_maps.splitlines() if ln.strip()]
            if filter.strip():
                flt = filter.strip().lower()
                lines = [ln for ln in lines if flt in ln.lower()]

            if output_path.strip():
                Path(output_path.strip()).write_text("\n".join(lines) + "\n", encoding="utf-8")

            return to_json(
                {
                    "ok": True,
                    "pid": pid,
                    "mode": "maps",
                    "count": len(lines),
                    "saved_to": output_path.strip() or None,
                    "maps": lines[:300],
                    "truncated": len(lines) > 300,
                }
            )

        # mode == "dump"
        start = parse_address(start_addr, hex_default=True)
        end = parse_address(end_addr, hex_default=True)
        if end <= start:
            return "ERROR: end_addr must be greater than start_addr"

        def _dump():
            client = manager.get_client()
            return client.memdump(int(pid), start, end)

        data = await manager.call(_dump)
        sha256 = hashlib.sha256(data).hexdigest()
        saved_to = None
        if output_path.strip():
            out_file = Path(output_path.strip())
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(data)
            saved_to = str(out_file)

        preview_len = min(len(data), 1024)
        return to_json(
            {
                "ok": True,
                "pid": pid,
                "mode": "dump",
                "start_hex": f"0x{start:x}",
                "end_hex": f"0x{end:x}",
                "size": len(data),
                "sha256": sha256,
                "saved_to": saved_to,
                "hex_preview": data[:preview_len].hex(),
                "preview_truncated": len(data) > preview_len,
            }
        )
    except Exception as exc:
        return format_error(exc)
