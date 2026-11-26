"""Comprehensive offline test suite for all Renef MCP v0.4.0 tools, resources, and prompts."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

import src.main  # noqa: F401 - ensures all tools/resources/prompts are registered
from src.app import mcp
from src.session import (
    ANDROID_BIN_DIR,
    BIN_DIR,
    DEVICE_AGENT_PATH,
    DEVICE_SERVER_PATH,
    RECIPES_DIR,
    manager,
)
from src.tools.adb.adb_app import adb_app
from src.tools.adb.adb_device_status import adb_device_status
from src.tools.adb.adb_devices import adb_devices
from src.tools.core.renef_attach import renef_attach
from src.tools.core.renef_command import renef_command
from src.tools.core.renef_events import renef_events
from src.tools.core.renef_exec import renef_exec
from src.tools.core.renef_list_apps import renef_list_apps
from src.tools.core.renef_load_script import renef_load_script
from src.tools.core.renef_ping import renef_ping
from src.tools.core.renef_reset import renef_reset
from src.tools.core.renef_resume import renef_resume
from src.tools.core.renef_rpc import renef_rpc
from src.tools.core.renef_spawn import renef_spawn
from src.tools.core.renef_verbose import renef_verbose
from src.tools.hook.renef_hook_generate import renef_hook_generate
from src.tools.hook.renef_hook_java import renef_hook_java
from src.tools.hook.renef_hook_native import renef_hook_native
from src.tools.hook.renef_hooks_list import renef_hooks_list
from src.tools.hook.renef_interceptor import renef_interceptor
from src.tools.hook.renef_native_call import renef_native_call
from src.tools.hook.renef_unhook import renef_unhook
from src.tools.java.renef_java_call import renef_java_call
from src.tools.java.renef_java_classes import renef_java_classes
from src.tools.java.renef_java_method_info import renef_java_method_info
from src.tools.java.renef_jni import renef_jni
from src.tools.memory.renef_mem_dump import renef_mem_dump
from src.tools.memory.renef_mem_manage import renef_mem_manage
from src.tools.memory.renef_mem_read import renef_mem_read
from src.tools.memory.renef_mem_search import renef_mem_search
from src.tools.memory.renef_mem_write import renef_mem_write
from src.tools.memory.renef_memdump_passive import renef_memdump_passive
from src.tools.module.renef_detect_framework import renef_detect_framework
from src.tools.module.renef_disassemble import renef_disassemble
from src.tools.module.renef_module_exports import renef_module_exports
from src.tools.module.renef_module_find import renef_module_find
from src.tools.module.renef_module_list import renef_module_list
from src.tools.module.renef_module_sections import renef_module_sections
from src.tools.module.renef_process import renef_process
from src.tools.search.renef_recipes import renef_recipes
from src.tools.search.technique_search import search_techniques
from src.tools.server.renef_port_forward import renef_port_forward
from src.tools.server.renef_server import renef_server
from src.tools.system.renef_file import renef_file
from src.tools.system.renef_kcov import renef_kcov
from src.tools.system.renef_os import renef_os
from src.tools.system.renef_syscall import renef_syscall


# ---------------------------------------------------------------------------
# Registration, Binaries, Resources & Prompts
# ---------------------------------------------------------------------------


async def test_mcp_server_registration_completeness():
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert len(tool_names) == 47
    for expected in (
        "renef_ping",
        "renef_spawn",
        "renef_resume",
        "renef_rpc",
        "renef_events",
        "renef_memdump_passive",
        "renef_mem_manage",
        "renef_disassemble",
        "renef_interceptor",
        "renef_native_call",
        "renef_java_classes",
        "renef_java_call",
        "renef_java_method_info",
        "renef_syscall",
        "renef_kcov",
        "renef_recipes",
        "renef_server",
    ):
        assert expected in tool_names

    resources = {str(r.uri) for r in await mcp.list_resources()}
    assert "renef://api-reference" in resources
    assert "renef://recipes" in resources
    assert "techniques://ssl_pinning" in resources

    prompts = {p.name for p in await mcp.list_prompts()}
    assert "renef_lua_guide" in prompts


async def test_resources_and_prompts_readable():
    api_ref = await mcp.read_resource("renef://api-reference")
    api_text = api_ref[0].content
    assert "Renef v0.4.0" in api_text
    assert "Interceptor.replace" in api_text
    assert "Module.disassemble" in api_text

    recipes_idx = await mcp.read_resource("renef://recipes")
    assert "ssl_pinning_bypass" in recipes_idx[0].content

    ssl_recipe = await mcp.read_resource("renef://recipes/ssl_pinning_bypass")
    assert "TrustManager" in ssl_recipe[0].content or "SSLContext" in ssl_recipe[0].content

    ssl_tech = await mcp.read_resource("techniques://ssl_pinning")
    assert "renef_detect_framework" in ssl_tech[0].content
    assert "renef_detect_platform" not in ssl_tech[0].content

    guide = await mcp.get_prompt("renef_lua_guide", {"task": "bypass ssl pinning"})
    assert "bypass ssl pinning" in guide.messages[0].content.text
    assert "NOT" in guide.messages[0].content.text


def test_v040_binaries_and_scripts_present():
    for rel in (
        "android/renef_server",
        "android/libagent.so",
        "android/renef",
        "android/renef-strace",
        "linux/renef",
        "linux/renef-strace",
        "macos-arm64/renef",
        "macos-arm64/renef-strace",
        "macos-x64/renef",
        "macos-x64/renef-strace",
    ):
        assert (BIN_DIR / rel).is_file(), f"Missing v0.4.0 binary: {rel}"

    assert (RECIPES_DIR / "ssl_pinning_bypass.lua").is_file()
    assert (RECIPES_DIR / "engine_capture.lua").is_file()
    assert (RECIPES_DIR / "taint_filter.lua").is_file()
    assert (ANDROID_BIN_DIR / "libagent.so").stat().st_size > 1_000_000


# ---------------------------------------------------------------------------
# Core & Session Tools
# ---------------------------------------------------------------------------


async def test_core_lifecycle_and_execution(mock_renef, tmp_path: Path):
    server, target = mock_renef

    ping = json.loads(await renef_ping())
    assert ping["ok"] is True
    assert ping["framed_protocol"] is True
    assert ping["active_session"] is False

    apps = json.loads(await renef_list_apps(filter="flutter"))
    assert apps["packages"] == ["com.test.flutter"]

    # Spawn with pause + hold (v0.4.0 spawn gate)
    sp = json.loads(await renef_spawn("com.example.app", pause=True, hold=True))
    assert sp["ok"] is True
    assert sp["pid"] == 4242
    assert sp["paused"] is True
    assert "spawn com.example.app --pause --hold" in server.commands

    resumed = json.loads(await renef_resume())
    assert resumed["ok"] is True
    assert "Resumed pid 4242" in resumed["reply"]
    assert manager.is_paused is False

    # Multiline exec & error propagation
    ok_res = json.loads(await renef_exec("PRINT_HELLO\n-- line 2 with // and ~"))
    assert ok_res["ok"] is True
    assert ok_res["output"] == "hello from lua"

    err_res = json.loads(await renef_exec('error("BOOM")'))
    assert err_res["ok"] is False
    assert err_res["error"] == "eval:1: boom"

    # RPC
    target.rpc["1 + 1"] = 2
    rpc_ok = json.loads(await renef_rpc("1 + 1"))
    assert rpc_ok == {"ok": True, "value": 2}

    target.rpc["bad()"] = RuntimeError("nil value")
    rpc_err = await renef_rpc("bad()")
    assert "ERROR [lua]" in rpc_err

    # Load script from host file
    script = tmp_path / "sample.lua"
    script.write_text("PRINT_HELLO\n", encoding="utf-8")
    loaded = json.loads(await renef_load_script(str(script)))
    assert loaded["ok"] is True
    assert loaded["scripts"][0]["output"] == "hello from lua"

    # Events channel (structured send() + hook text)
    target.pending_output_lines = ["[hook] hit open('/etc/hosts')"]
    target.pending_events = [{"type": "finding", "secret": "xyz"}]
    ev = json.loads(await renef_events(wait_ms=10))
    assert ev["event_count"] == 1
    assert ev["output_line_count"] == 1
    assert ev["events"][0]["secret"] == "xyz"
    assert ev["output"][0] == "[hook] hit open('/etc/hosts')"

    # Verbose & raw command
    verb = json.loads(await renef_verbose(True))
    assert verb["ok"] is True
    assert "ON" in verb["reply"]
    assert "pong" in await renef_command("ping")

    # Attach by package name resolves PID via OS.getpid()
    att = json.loads(await renef_attach("com.example.app"))
    assert att["ok"] is True
    assert att["pid"] == 4242

    # Session reset clears session
    rst = json.loads(await renef_reset(mode="session"))
    assert rst["ok"] is True
    assert manager.get_session() is None


# ---------------------------------------------------------------------------
# Hooking, Interceptor & NativeFunction
# ---------------------------------------------------------------------------


async def test_hook_tools(mock_renef):
    server, target = mock_renef
    await renef_spawn("com.example.app")

    # Quick hookn
    h1 = json.loads(await renef_hook_native("libc.so", "open"))
    assert h1["ok"] is True
    assert h1["mode"] == "hookn"
    assert "hookn libc.so open" in server.commands

    # Custom native hook with PLT/GOT caller & async validation
    bad_async = await renef_hook_native("libc.so", "0x100", on_enter="print(1)", on_leave="return 0", asynchronous=True)
    assert "ERROR:" in bad_async

    h2 = json.loads(
        await renef_hook_native("libc.so", "0x100", on_enter="print(args[0])", caller="*", asynchronous=True)
    )
    assert h2["ok"] is True
    assert h2["hook_type"] == "pltgot"
    assert h2["asynchronous"] is True

    # Deferred hook on not-yet-loaded lib
    target.defer_next_hook = True
    h3 = json.loads(await renef_hook_native("libfuture.so", "0x200", on_enter="print(1)"))
    assert h3["ok"] is True
    assert h3["deferred"] is True

    # Java hook with dot normalization, skip_original, and JNI.string return
    hj = json.loads(
        await renef_hook_java(
            "com.example.Security",
            "checkPin",
            "(Ljava/lang/String;)V",
            skip_original=True,
        )
    )
    assert hj["ok"] is True
    assert hj["class"] == "com/example/Security"
    assert hj["skip_original"] is True

    # Java hook without signature (reflection all-overloads discovery)
    hj_all = json.loads(await renef_hook_java("com/example/App", "getToken"))
    assert hj_all["ok"] is True
    assert hj_all["signature"] == "(all overloads)"
    assert hj_all["installed"] == 2
    assert len(hj_all["signatures"]) == 2

    # Interceptor replace (int, bare Lua body auto-wrapped, and revert)
    rep = json.loads(await renef_interceptor("replace", "libc.so", "0x4400", replacement="0"))
    assert rep["ok"] is True
    rep_body = json.loads(await renef_interceptor("replace", "libc.so", "0x4400", replacement="return 42"))
    assert rep_body["ok"] is True
    rev = json.loads(await renef_interceptor("revert", "libc.so", "0x4400"))
    assert rev["ok"] is True

    # NativeFunction (and NULL address safety check)
    assert "ERROR:" in await renef_native_call("0x0")
    nf = json.loads(
        await renef_native_call("0x7a00004400", ret_type="int", arg_types=["pointer"], args=["0x7000200000"])
    )
    assert nf["ok"] is True
    assert nf["result"] == 5

    # Hooks list & unhook (rejects invalid IDs so atoi("bad") never removes hook 0!)
    listed = await renef_hooks_list()
    assert "Active hooks:" in listed
    assert "Java hooks:" in listed

    assert "ERROR:" in await renef_unhook("invalid_id")
    un_j = json.loads(await renef_unhook("j0"))
    assert un_j["ok"] is True
    assert "unhook j0" in server.commands

    un_all = json.loads(await renef_unhook("all"))
    assert un_all["ok"] is True

    # hookgen
    gen = await renef_hook_generate("libc.so", "open")
    assert "hook(" in gen


# ---------------------------------------------------------------------------
# Memory & Passive Memdump
# ---------------------------------------------------------------------------


async def test_memory_and_passive_memdump(mock_renef, tmp_path: Path):
    # Passive memdump works WITHOUT spawning/attaching!
    maps_res = json.loads(await renef_memdump_passive(pid=4242, mode="maps", filter="libapp"))
    assert maps_res["ok"] is True
    assert maps_res["count"] == 1
    assert "libapp.so" in maps_res["maps"][0]

    dump_file = tmp_path / "dump.bin"
    dump_res = json.loads(
        await renef_memdump_passive(
            pid=4242, mode="dump", start_addr="0x1000", end_addr="0x1008", output_path=str(dump_file)
        )
    )
    assert dump_res["ok"] is True
    assert dump_res["size"] == 8
    assert dump_file.read_bytes() == b"\x7fELF\x00\x00\x00\x00"

    # Active session memory tools
    await renef_spawn("com.example.app")

    r_hex = json.loads(await renef_mem_read("0x7a00000000", size=8, format="hex"))
    assert r_hex["ok"] is True
    assert r_hex["hex"] == "7f454c4602010100"

    r_str = json.loads(await renef_mem_read("0x7a00000000", format="string"))
    assert r_str["value"] == "hello_renef"

    r_hd = json.loads(await renef_mem_read("0x7a00000000", size=16, format="hexdump"))
    assert ".ELF" in r_hd["hexdump"]

    r_u32 = json.loads(await renef_mem_read("0x7a00000000", format="u32"))
    assert r_u32["value"] == 0x464C457F

    w_hex = json.loads(await renef_mem_write("0x7a00000000", "C0 03 5F D6", type="hex", patch=True))
    assert w_hex["ok"] is True
    assert w_hex["method"] == "patch"

    w_u32 = json.loads(await renef_mem_write("0x7a00000000", "0xdeadbeef", type="u32"))
    assert w_u32["ok"] is True
    assert w_u32["bytes_written"] == 4

    srch = json.loads(await renef_mem_search("Hello", lib_name="libtarget.so"))
    assert srch["ok"] is True
    assert srch["total_matches"] == 1
    assert srch["matches"][0]["addr_hex"] == "0x7f10001234"

    md_dis = await renef_mem_dump("0x7a00004400", size=8, disassemble=True)
    assert "stp" in md_dis

    alloc = json.loads(await renef_mem_manage("alloc", size=4096, prot="rwx"))
    assert alloc["address_hex"] == "0x7000100000"
    alloc_s = json.loads(await renef_mem_manage("alloc_str", text="hello"))
    assert alloc_s["address_hex"] == "0x7000200000"
    prot = json.loads(await renef_mem_manage("protect", address="0x7000100000", size=4096, prot="r-x"))
    assert prot["ok"] is True
    freed = json.loads(await renef_mem_manage("free", address="0x7000100000", size=4096))
    assert freed["ok"] is True


# ---------------------------------------------------------------------------
# Module, Disassembly, Framework & Process
# ---------------------------------------------------------------------------


async def test_module_and_process_tools(mock_renef):
    _, target = mock_renef
    await renef_spawn("com.example.app")

    mods = json.loads(await renef_module_list(filter="flutter"))
    assert mods["total"] == 1
    assert mods["modules"][0]["name"] == "libflutter.so"

    # Verify negative signed 64-bit tagged pointer becomes unsigned hex
    target.rpc['Module.find("tagged.so")'] = 0xB400007C14003E7E - (1 << 64)
    found = json.loads(await renef_module_find("tagged.so"))
    assert found["found"] is True
    assert found["base_hex"] == "0xb400007c14003e7e"

    exps = json.loads(await renef_module_exports("libc.so", pattern="open*"))
    assert exps["total_matches"] == 2
    assert exps["symbols"][0]["name"] == "open"

    syms = json.loads(await renef_module_exports("libc.so", pattern="__internal*", include_symbols=True))
    assert syms["table"] == "symtab"
    assert syms["total_matches"] == 1

    secs = await renef_module_sections("libc.so")
    assert ".text" in secs

    dis = json.loads(await renef_disassemble("0x7a00004400", count=3))
    assert dis["count"] == 3
    assert dis["instructions"][1]["is_call"] is True
    assert "bl #0x7a00005000" in dis["listing"]

    fw = json.loads(await renef_detect_framework())
    assert fw["primary_framework"] == "flutter"
    assert fw["ssl_pinning_resource"] == "techniques://ssl_pinning/flutter"

    p_info = json.loads(await renef_process("info"))
    assert p_info["pid"] == 4242
    assert p_info["thread_count"] == 3

    p_ranges = json.loads(await renef_process("ranges", filter="r-xp"))
    assert p_ranges["total"] == 1

    p_bt = json.loads(await renef_process("backtrace"))
    assert p_bt["frames"][0]["module"] == "libc.so"


# ---------------------------------------------------------------------------
# Java, JNI, Syscall, File, OS, KCov & Recipes
# ---------------------------------------------------------------------------


async def test_java_jni_and_system_tools(mock_renef):
    await renef_spawn("com.example.app")

    # Java
    clz = json.loads(await renef_java_classes(pattern="pinning"))
    assert clz["classes"] == ["com.example.app.net.PinningClient"]

    st_call = json.loads(
        await renef_java_call("java.lang.System", "currentTimeMillis", "()J")
    )
    assert st_call["value"] == 1700000000000

    ctor = json.loads(
        await renef_java_call("java/io/File", constructor=True, signature="(Ljava/lang/String;)V", args=["/tmp"])
    )
    assert ctor["type"] == "java_object"
    assert ctor["handle"] == 1
    assert ctor["raw_hex"] == "0x12c04080"

    inst = json.loads(
        await renef_java_call(instance_handle=1, method_name="exists", signature="()Z")
    )
    assert inst["value"] is True

    rel = json.loads(await renef_java_call(instance_handle=1, release=True))
    assert rel["ok"] is True
    assert rel["released_handle"] == 1

    mi = json.loads(await renef_java_method_info("com.example.Bridge", "nativeFn", "()V"))
    assert mi["native"] is True
    assert mi["bound"] is True
    assert mi["jni_hex"] == "0x7b00009999"

    # JNI
    jnew = json.loads(await renef_jni("new_string", value="abc"))
    assert jnew["ref_hex"] == "0x12c08888"
    jget = json.loads(await renef_jni("get_string", ref="0x12c08888"))
    assert jget["value"] == "secret_java_str"
    jlen = json.loads(await renef_jni("string_length", ref="0x12c08888"))
    assert jlen["length"] == 15
    jdel = json.loads(await renef_jni("delete_ref", ref="0x12c08888"))
    assert jdel["ok"] is True

    # Syscall
    s_list = json.loads(await renef_syscall("list"))
    assert s_list["count"] == 2
    s_tr = json.loads(await renef_syscall("trace", syscalls=["openat", "read"], caller="libapp.so"))
    assert s_tr["ok"] is True
    s_cat = json.loads(await renef_syscall("trace", category="file"))
    assert s_cat["ok"] is True
    s_act = json.loads(await renef_syscall("active"))
    assert s_act["active_traces"][0]["name"] == "openat"
    s_un = json.loads(await renef_syscall("untrace", syscalls=["openat"]))
    assert s_un["ok"] is True
    s_stop = json.loads(await renef_syscall("stop"))
    assert s_stop["ok"] is True

    # File
    assert json.loads(await renef_file("exists", path="/etc/hosts"))["exists"] is True
    assert "token" in json.loads(await renef_file("read", path="/data/x.xml"))["content"]
    assert json.loads(await renef_file("readlink", path="/proc/self/exe"))["target"] == "/system/bin/app_process64"
    assert "secret.db" in json.loads(await renef_file("fdpath", fd=5))["path"]
    assert json.loads(await renef_file("write", path="/data/local/tmp/out.bin", address="0x7a00000000", size=4096))["ok"] is True

    # OS
    assert json.loads(await renef_os("getpid"))["pid"] == 4242
    assert json.loads(await renef_os("listdir", path="/proc/self/task"))["entries"] == ["4242", "4243"]
    assert json.loads(await renef_os("kill", pid=4242, signal=0))["ok"] is True
    assert json.loads(await renef_os("tgkill", pid=4242, tid=4243, signal=0))["ok"] is True

    # KCov
    assert json.loads(await renef_kcov("start", buf_size=65536))["ok"] is True
    assert json.loads(await renef_kcov("count"))["count"] == 42
    assert len(json.loads(await renef_kcov("collect"))["pcs"]) == 2
    assert json.loads(await renef_kcov("edges"))["unique_edges"] == 2
    assert json.loads(await renef_kcov("reset"))["ok"] is True
    assert json.loads(await renef_kcov("stop"))["ok"] is True

    # Recipes + Techniques
    rec_list = json.loads(await renef_recipes("list"))
    assert rec_list["recipes_count"] >= 6
    rec_src = await renef_recipes("get", name="taint_filter")
    assert "taint_filter" in rec_src
    assert "ERROR:" in await renef_recipes("get", name="../../etc/passwd")
    rec_run = json.loads(await renef_recipes("run", name="taint_filter"))
    assert rec_run["ok"] is True

    tech = await search_techniques("OkHttp", platform="android")
    assert "OkHttp" in tech


# ---------------------------------------------------------------------------
# Server & ADB Tools (mocked ADB subprocess)
# ---------------------------------------------------------------------------


async def test_server_deploy_uses_v040_libagent_path(monkeypatch):
    calls = []

    async def fake_adb(*args, **kwargs):
        calls.append(args)
        if args[:2] == ("shell", "pidof"):
            return 0, "9876"
        if args[0] == "shell" and "test -f" in args[1]:
            return 0, "exists"
        if args[:2] == ("forward", "--list"):
            return 0, "emulator-5554 tcp:1907 localabstract:com.android.internal.os.RuntimeInit"
        return 0, "ok"

    monkeypatch.setattr("src.tools.server.renef_server.run_adb", fake_adb)
    monkeypatch.setattr("src.tools.server.renef_port_forward.run_adb", fake_adb)

    dep = json.loads(await renef_server("deploy"))
    assert dep["ok"] is True
    assert dep["renef_server"]["path"] == DEVICE_SERVER_PATH
    assert dep["libagent"]["path"] == DEVICE_AGENT_PATH
    assert DEVICE_AGENT_PATH == "/data/local/tmp/libagent.so"
    # Verify chmod 777 & SELinux chcon were invoked on /data/local/tmp/libagent.so
    assert ("shell", "chmod", "777", "/data/local/tmp/libagent.so") in calls
    assert any("chcon u:object_r:app_data_file:s0 /data/local/tmp/libagent.so" in str(c) for c in calls)

    st = json.loads(await renef_server("status"))
    assert st["renef_server_deployed"] is True
    assert st["libagent_deployed"] is True
    assert st["running"] is True

    fwd = json.loads(await renef_port_forward("status"))
    assert fwd["count"] == 1
    fwd_g = json.loads(await renef_port_forward("add", gadget_pid=5555))
    assert fwd_g["remote"] == "localabstract:renef_pl_5555"


async def test_adb_tools(monkeypatch):
    async def fake_adb(*args, **kwargs):
        if args[0] == "devices":
            return 0, "List of devices attached\nemulator-5554 device product:sdk"
        if args == ("shell", "whoami"):
            return 0, "shell"
        if args == ("shell", "su", "-c", "id"):
            return 0, "uid=0(root) gid=0(root)"
        if args == ("shell", "magisk", "-v"):
            return 0, "27.0:MAGISK"
        if args == ("shell", "getenforce"):
            return 0, "Permissive"
        if args[:3] == ("shell", "pm", "list"):
            return 0, "package:com.example.app\npackage:com.android.settings"
        if args[0] == "shell" and "mCurrentFocus" in args[1]:
            return 0, "mCurrentFocus=Window{abc u0 com.example.app/com.example.app.MainActivity}"
        if args[0] == "shell" and "Recent #0" in args[1]:
            return 0, "mRootProcess=ProcessRecord{def 4242:com.example.app/u0a123}"
        return 0, "ok"

    monkeypatch.setattr("src.tools.adb.adb_devices.run_adb", fake_adb)
    monkeypatch.setattr("src.tools.adb.adb_device_status.run_adb", fake_adb)
    monkeypatch.setattr("src.tools.adb.adb_app.run_adb", fake_adb)

    assert "emulator-5554" in await adb_devices()

    dev_st = json.loads(await adb_device_status(selinux_action="disable"))
    assert dev_st["rooted"] is True
    assert dev_st["selinux"] == "Permissive"
    assert dev_st["selinux_change"]["applied"] is True

    cur = json.loads(await adb_app("current"))
    assert cur["package"] == "com.example.app"
    assert cur["pid"] == 4242

    lst = json.loads(await adb_app("list", filter="example"))
    assert lst["packages"] == ["com.example.app"]

    assert json.loads(await adb_app("start", package_name="com.example.app"))["ok"] is True
    assert json.loads(await adb_app("stop", package_name="com.example.app"))["ok"] is True


async def test_mcp_protocol_call_tool_and_error_paths(mock_renef, monkeypatch):
    # Calling a session-dependent tool before spawn/attach returns clean error
    no_sess = await renef_exec("print(1)")
    assert "ERROR [renef]: No active target session" in no_sess

    # Sessionless hookgen with explicit offset works without an active session
    assert "hook(" in await renef_hook_generate("libc.so", "0x4400")

    # End-to-end via MCPServer.call_tool
    ping_call = await mcp.call_tool("renef_ping", {})
    assert not ping_call.is_error
    ping_data = json.loads(ping_call.content[0].text)
    assert ping_data["ok"] is True

    # Spawn with pause=True, hold=False auto-clears is_paused after exec
    await renef_spawn("com.example.app", pause=True, hold=False)
    assert manager.is_paused is True
    await renef_exec("PRINT_HELLO")
    assert manager.is_paused is False

    # NULL address guards
    assert "ERROR:" in await renef_mem_write("0x0", "9090")
    assert "ERROR:" in await renef_mem_dump("0x0", size=16)

    spawn_call = await mcp.call_tool("renef_spawn", {"package_name": "com.example.app"})
    assert json.loads(spawn_call.content[0].text)["pid"] == 4242

    # Hard reset with redeploy uses v0.4.0 /data/local/tmp/libagent.so path
    adb_calls = []

    async def fake_reset_adb(*args, **kwargs):
        adb_calls.append(args)
        if args[:2] == ("shell", "pidof"):
            return 0, "7777"
        return 0, "ok"

    monkeypatch.setattr("src.tools.core.renef_reset.run_adb", fake_reset_adb)
    hard = json.loads(await renef_reset(mode="hard", redeploy=True, kill_app="com.example.app"))
    assert hard["ok"] is True
    assert any(DEVICE_AGENT_PATH in str(c) for c in adb_calls)
    assert any("chcon u:object_r:app_data_file:s0 /data/local/tmp/libagent.so" in str(c) for c in adb_calls)

