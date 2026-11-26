"""Protocol, transport, quoting, and McpSession event-separation tests."""

import pytest

from src.renef_client.errors import RenefConnectionError, RenefTimeoutError
from src.renef_client.lua import quote, to_lua
from src.renef_client.transport import Connection, ResponseReader
from src.session import (
    McpClient,
    normalize_java_class,
    parse_address,
    parse_hex_bytes,
    parse_target_offset_or_symbol,
    u64,
)
from tests.mock_server import FakeRenefTarget, MockServer, Reply


def test_lua_quote_escapes_special_chars():
    for sample in ['plain', 'has "quotes"', "back\\slash", "line1\nline2", "nul\x00byte", "café"]:
        lit = quote(sample)
        assert lit.startswith('"') and lit.endswith('"')
        assert "\n" not in lit
        assert '"' not in lit[1:-1]


def test_to_lua_and_u64():
    assert to_lua(None) == "nil"
    assert to_lua(True) == "true"
    assert to_lua(0xB400007C14003E7E) == "0xb400007c14003e7e"
    assert u64(-1) == 0xFFFFFFFFFFFFFFFF
    assert u64(0xB400007C14003E7E - (1 << 64)) == 0xB400007C14003E7E


def test_parsing_helpers():
    assert parse_address("0x1234") == 0x1234
    assert parse_address("1000") == 1000
    assert parse_address("1000", hex_default=True) == 0x1000
    assert parse_address("deadbeef") == 0xDEADBEEF
    assert parse_target_offset_or_symbol("0x4400") == 0x4400
    assert parse_target_offset_or_symbol("open") == "open"
    assert parse_hex_bytes("C0 03 5F D6") == bytes.fromhex("C0035FD6")
    assert parse_hex_bytes("\\x7f\\x45\\x4c\\x46") == b"\x7fELF"
    assert normalize_java_class("com.example.Main") == "com/example/Main"
    assert normalize_java_class("Lcom/example/Main;") == "com/example/Main"


def test_response_reader_demux_and_pending_events():
    reader = ResponseReader()
    reader.sent(1)
    reader.sent(2)
    reader.feed(b"stale\x1e@done 1\nreal_reply\n\x1e@done 2 ev=7\n")
    out = bytearray()
    assert reader.poll(2, out)
    assert bytes(out) == b"real_reply\n"
    assert reader.pending_events == 7


def test_framed_and_legacy_transport_and_timeout_isolation():
    def handler(cmd: str):
        if cmd == "ping":
            return "pong\n"
        if cmd == "slow":
            return Reply("slow-reply\n", delay=0.5)
        return f"echo:{cmd}\n"

    with MockServer(handler, framing=True) as srv:
        conn = Connection("127.0.0.1", srv.port)
        assert conn.framed
        with pytest.raises(RenefTimeoutError):
            conn.request("slow", timeout=0.15)
        # Late reply for `slow` must be discarded and not returned for `fast`
        assert conn.request("fast", timeout=5.0) == b"echo:fast\n"
        conn.close()

    with MockServer(handler, framing=False) as srv:
        conn = Connection("127.0.0.1", srv.port)
        assert not conn.framed
        assert conn.request("hi") == b"echo:hi\n"
        with pytest.raises(RenefConnectionError):
            conn.request("multi\nline")
        conn.close()


def test_mcp_session_separates_eval_output_from_hook_events():
    target = FakeRenefTarget()
    target.announce_pending = True
    with MockServer(target, framing=True) as srv:
        client = McpClient("127.0.0.1", srv.port)
        session = client.spawn_app("com.example.app")

        # eval() output must stay in eval result and NOT pollute hook output buffer
        res = session.eval("PRINT_HELLO")
        assert res.ok
        assert res.output == "hello from lua"
        assert session.pending_counts() == (0, 0)

        # Simulate hook output + send() event held on server while another command runs
        target.pending_output_lines = ["[hook open] /data/secret"]
        target.pending_events = [{"type": "key_found", "algo": "AES"}]

        hooks_text = session.hooks()
        assert "Active hooks:" in hooks_text
        # Held events were auto-drained into session buffers via `ev=2` -> `events 0`
        assert session.pending_counts() == (1, 1)

        events, output = session.poll_all(0)
        assert events == [{"type": "key_found", "algo": "AES"}]
        assert output == ["[hook open] /data/secret"]
        # Subsequent poll is empty
        assert session.poll_all(0) == ([], [])
        client.close()
