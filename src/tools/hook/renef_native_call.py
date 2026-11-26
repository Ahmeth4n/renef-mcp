from __future__ import annotations

from typing import Any, List, Optional

from src.app import mcp
from src.session import format_error, manager, parse_address, to_json


@mcp.tool()
async def renef_native_call(
    address: str,
    ret_type: str = "pointer",
    arg_types: Optional[List[str]] = None,
    args: Optional[List[Any]] = None,
    timeout: float = 30.0,
) -> str:
    """Call a native ARM64 function directly inside the target process via `NativeFunction`.

    Supports up to 8 integer/pointer args (x0-x7) and 8 float/double args (d0-d7).
    Explicit calls via `NativeFunction` DO trigger installed hooks on the target address.

    Supported types for `ret_type` and `arg_types`:
    `"int"`, `"long"`, `"pointer"`, `"bool"`, `"string"`, `"void"`, `"float"`, `"double"`.

    Args:
        address: Target function address (e.g., "0x7f8a12340")
        ret_type: Return type (default: "pointer")
        arg_types: Optional list of argument types (e.g., ["pointer", "int"])
        args: Optional list of argument values (ints, hex address strings starting with "0x",
              floats, bools, or strings). Note: if an argument's declared type is "pointer" and
              you pass a hex string like "0x7f0000", it is converted to an integer pointer.
        timeout: Call timeout in seconds (default: 30.0)

    Returns:
        JSON object with `ok`, `result`, and hex formatting for pointer returns
    """
    try:
        addr = parse_address(address)
        if addr == 0:
            return "ERROR: address must be non-zero (calling 0x0 would crash the target process)"
        types_list = list(arg_types or [])
        raw_args = list(args or [])

        # Convert hex pointer strings when arg_type is pointer/long/int
        coerced_args: List[Any] = []
        for idx, val in enumerate(raw_args):
            atype = types_list[idx] if idx < len(types_list) else "pointer"
            if isinstance(val, str) and atype in ("pointer", "int", "long") and val.strip().lower().startswith("0x"):
                coerced_args.append(int(val.strip(), 16))
            else:
                coerced_args.append(val)

        def _call():
            session = manager.require_session()
            fn = session.native_function(addr, ret=ret_type, args=types_list)
            return fn(*coerced_args, timeout=timeout)

        result = await manager.call(_call)
        payload: dict[str, Any] = {
            "ok": True,
            "address": f"0x{addr:x}",
            "ret_type": ret_type,
            "result": result,
        }
        if ret_type == "pointer" and isinstance(result, int):
            payload["result_hex"] = f"0x{result:x}"
        return to_json(payload)
    except Exception as exc:
        return format_error(exc)
