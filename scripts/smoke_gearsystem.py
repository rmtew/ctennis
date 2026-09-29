"""Check Gearsystem's headless MCP stdio interface without third-party packages."""

import argparse
import configparser
import base64
import hashlib
import json
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read_messages(pipe, messages):
    for line in pipe:
        try:
            messages.put(json.loads(line))
        except json.JSONDecodeError:
            messages.put({"unparsed_output": line.strip()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--button", choices=("up", "down", "left", "right", "start", "1", "2"))
    parser.add_argument("--hold-frames", type=int, default=10)
    parser.add_argument("--after-frames", type=int, default=120)
    parser.add_argument("--late-button", choices=("up", "down", "left", "right", "start", "1", "2"))
    parser.add_argument("--late-hold-frames", type=int, default=30)
    parser.add_argument("--late-after-frames", type=int, default=0)
    parser.add_argument("--trace-cpu", action="store_true")
    parser.add_argument("--cpu-window-start", type=int,
                        help="Trace one reset frame starting at this 1-based frame number")
    parser.add_argument("--cpu-window-frames", type=int, default=1,
                        help="Number of consecutive frames to include in --cpu-window-start")
    parser.add_argument("--cpu-window-button", choices=("up", "down", "left", "right", "start", "1", "2"))
    parser.add_argument("--hardware-frames", type=int, help="Capture VDP/PSG trace and VRAM after this many reset frames")
    parser.add_argument("--hardware-button", choices=("up", "down", "left", "right", "start", "1", "2"))
    parser.add_argument("--hardware-press-frame", type=int, default=120)
    parser.add_argument("--hardware-hold-frames", type=int, default=300)
    parser.add_argument("--show-input-tools", action="store_true")
    args = parser.parse_args()
    if args.cpu_window_start is not None and (args.cpu_window_start < 1 or args.button or args.hardware_frames is not None or args.trace_cpu):
        parser.error("--cpu-window-start must be positive and cannot be combined with input or other traces")
    if args.cpu_window_frames < 1 or (args.cpu_window_frames != 1 and args.cpu_window_start is None):
        parser.error("--cpu-window-frames requires --cpu-window-start and must be positive")
    if args.cpu_window_button and args.cpu_window_start is None:
        parser.error("--cpu-window-button requires --cpu-window-start")
    if args.hardware_frames is not None and (args.hardware_frames < 1 or args.button or args.trace_cpu):
        parser.error("--hardware-frames must be positive and cannot be combined with --button or --trace-cpu")
    if args.hardware_button and (args.hardware_frames is None or args.hardware_press_frame < 0 or
                                 args.hardware_hold_frames < 1 or
                                 args.hardware_frames <= args.hardware_press_frame + args.hardware_hold_frames):
        parser.error("--hardware-button requires a capture extending past its positive hold interval")
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / "config.local.ini", encoding="utf-8")
    emulator = Path(config["tools"]["gearsystem"])
    cartridge = Path(config["inputs"]["cartridge"])
    if not emulator.is_file():
        raise FileNotFoundError(emulator)
    if not cartridge.is_file():
        raise FileNotFoundError(cartridge)

    report_dir = ROOT / "build" / "smoke"
    report_dir.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(cartridge.read_bytes()).hexdigest()
    staged_cartridge = report_dir / "champion-tennis.sg"
    shutil.copyfile(cartridge, staged_cartridge)
    if hashlib.sha256(staged_cartridge.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Staged cartridge bytes differ from source")
    with (report_dir / "gearsystem.stderr.log").open("w", encoding="utf-8") as errors:
        process = subprocess.Popen(
            [str(emulator), "--headless", "--mcp-stdio", "--portable"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=errors,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        messages = queue.Queue()
        threading.Thread(target=read_messages, args=(process.stdout, messages), daemon=True).start()
        next_id = 0

        def request(method, params):
            nonlocal next_id
            next_id += 1
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": next_id, "method": method, "params": params}) + "\n")
            process.stdin.flush()
            while True:
                response = messages.get(timeout=20)
                if response.get("id") == next_id:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response["result"]
                if "unparsed_output" in response:
                    raise RuntimeError(response)

        try:
            initialization = request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "champion-tennis-smoke", "version": "0.1"},
                },
            )
            process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            process.stdin.flush()
            listed = request("tools/list", {})
            tools = {tool["name"]: tool for tool in listed["tools"]}
            if args.show_input_tools:
                print(json.dumps({name: tool for name, tool in tools.items()
                                  if "input" in name or "key" in name or "controller" in name}, indent=2))
                return
            needed = {"load_media", "debug_step_frame", "read_memory", "controller_button", "get_screenshot"}
            missing = sorted(needed - tools.keys())
            if missing:
                raise RuntimeError(f"Missing required MCP tools: {missing}")
            loaded = request("tools/call", {"name": "load_media", "arguments": {"file_path": str(staged_cartridge)}})
            if loaded.get("isError"):
                raise RuntimeError(f"Cartridge load failed: {loaded.get('content')}")
            media = request("tools/call", {"name": "get_media_info", "arguments": {}})
            media_info = json.loads(media["content"][0]["text"])
            if not media_info.get("is_sg1000"):
                raise RuntimeError(f"Gearsystem did not select SG-1000 mode: {media_info}")
            paused = request("tools/call", {"name": "debug_pause", "arguments": {}})
            reset = request("tools/call", {"name": "debug_reset", "arguments": {}})
            status = request("tools/call", {"name": "debug_get_status", "arguments": {}})
            areas = request("tools/call", {"name": "list_memory_areas", "arguments": {}})
            hardware_trace_data = None
            hardware_vdp_registers = None
            hardware_psg_status = None
            if args.cpu_window_start is not None:
                before_frames = args.cpu_window_start - 1
                current_frame = 0
                release_frame = args.hardware_press_frame + args.hardware_hold_frames
                while current_frame < before_frames:
                    if args.cpu_window_button and current_frame == args.hardware_press_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.cpu_window_button, "action": "press"}})
                    if args.cpu_window_button and current_frame == release_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.cpu_window_button, "action": "release"}})
                    next_event = (args.hardware_press_frame if current_frame < args.hardware_press_frame
                                  else release_frame if current_frame < release_frame
                                  else before_frames) if args.cpu_window_button else before_frames
                    chunk = min(before_frames - current_frame, next_event - current_frame)
                    request("tools/call", {"name": "debug_step_frame", "arguments": {
                        "frames": chunk, "mode": "sync"}})
                    current_frame += chunk
                before = request("tools/call", {"name": "read_memory", "arguments": {
                    "area": 7, "offset": "0080", "size": 16}})
                lines = []
                frame_counts = []
                sequence = 0
                for frame_offset in range(args.cpu_window_frames):
                    if args.cpu_window_button and current_frame == args.hardware_press_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.cpu_window_button, "action": "press"}})
                    if args.cpu_window_button and current_frame == release_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.cpu_window_button, "action": "release"}})
                    request("tools/call", {"name": "set_trace_log", "arguments": {
                        "enabled": True, "output": "memory", "memory_size": "5M",
                        "filters": ["cpu.instructions"],
                    }})
                    request("tools/call", {"name": "debug_step_frame", "arguments": {
                        "frames": 1, "mode": "sync"}})
                    current_frame += 1
                    frame_lines = []
                    while True:
                        page = request("tools/call", {"name": "get_trace_log", "arguments": {
                            "start": sequence, "count": 1000}})
                        parsed = json.loads(page["content"][0]["text"])
                        if parsed.get("overrun"):
                            raise RuntimeError(f"CPU trace overran before sequence {sequence}")
                        frame_lines.extend(parsed["lines"])
                        sequence = parsed["next_sequence"]
                        if sequence >= parsed["total_logged"]:
                            break
                    request("tools/call", {"name": "set_trace_log", "arguments": {"enabled": False}})
                    lines.extend(frame_lines)
                    frame_counts.append({"frame": args.cpu_window_start + frame_offset,
                                         "count": len(frame_lines)})
                after = request("tools/call", {"name": "read_memory", "arguments": {
                    "area": 7, "offset": "0080", "size": 16}})
                window = {"frame": args.cpu_window_start, "frames": args.cpu_window_frames,
                          "button": args.cpu_window_button,
                          "press_frame": args.hardware_press_frame if args.cpu_window_button else None,
                          "release_frame": release_frame if args.cpu_window_button else None,
                          "frame_counts": frame_counts, "count": len(lines),
                          "ram_c080_before": json.loads(before["content"][0]["text"])["data"],
                          "ram_c080_after": json.loads(after["content"][0]["text"])["data"],
                          "lines": lines}
                trace_name = (f"cpu-window-reset-{args.cpu_window_start}.json"
                              if args.cpu_window_frames == 1 else
                              f"cpu-window-reset-{args.cpu_window_start}-{args.cpu_window_start + args.cpu_window_frames - 1}.json")
                if args.cpu_window_button:
                    trace_name = trace_name.removesuffix(".json") + f"-button{args.cpu_window_button}.json"
                (report_dir / trace_name).write_text(
                    json.dumps(window, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({k: v for k, v in window.items() if k != "lines"}, indent=2))
                return
            if args.hardware_frames is None:
                stepped = request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": 120, "mode": "sync"}})
            else:
                request("tools/call", {"name": "set_trace_log", "arguments": {
                    "enabled": True, "output": "memory", "memory_size": "5M",
                    "filters": ["vdp.registers", "vdp.data", "vdp.status", "psg.tone",
                                "psg.volume", "psg.noise", "cpu.interrupts"],
                }})
                lines = []
                sequence = 0
                remaining = args.hardware_frames
                current_frame = 0
                release_frame = args.hardware_press_frame + args.hardware_hold_frames
                while remaining:
                    if args.hardware_button and current_frame == args.hardware_press_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.hardware_button, "action": "press"}})
                    if args.hardware_button and current_frame == release_frame:
                        request("tools/call", {"name": "controller_button", "arguments": {
                            "player": 1, "button": args.hardware_button, "action": "release"}})
                    next_event = (args.hardware_press_frame if current_frame < args.hardware_press_frame
                                  else release_frame if current_frame < release_frame
                                  else args.hardware_frames) if args.hardware_button else args.hardware_frames
                    chunk = min(remaining, 10, next_event - current_frame)
                    stepped = request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": chunk, "mode": "sync"}})
                    remaining -= chunk
                    current_frame += chunk
                    while True:
                        page = request("tools/call", {"name": "get_trace_log", "arguments": {"start": sequence, "count": 1000}})
                        parsed = json.loads(page["content"][0]["text"])
                        if parsed.get("overrun"):
                            raise RuntimeError(f"Hardware trace overran before sequence {sequence}")
                        lines.extend(parsed["lines"])
                        next_sequence = parsed["next_sequence"]
                        if next_sequence < sequence:
                            raise RuntimeError("Hardware trace sequence went backwards")
                        sequence = next_sequence
                        if sequence >= parsed["total_logged"]:
                            break
                request("tools/call", {"name": "set_trace_log", "arguments": {"enabled": False}})
                hardware_trace_data = {"frames": args.hardware_frames,
                                       "button": args.hardware_button,
                                       "press_frame": args.hardware_press_frame if args.hardware_button else None,
                                       "release_frame": release_frame if args.hardware_button else None,
                                       "count": len(lines),
                                       "last_sequence": sequence, "lines": lines}
                suffix = f"-button{args.hardware_button}" if args.hardware_button else ""
                (report_dir / f"hardware-trace-reset-{args.hardware_frames}{suffix}.json").write_text(
                    json.dumps(hardware_trace_data, indent=2) + "\n", encoding="utf-8")
                hardware_vdp_registers = request("tools/call", {"name": "get_vdp_registers", "arguments": {}})
                hardware_psg_status = request("tools/call", {"name": "get_psg_status", "arguments": {}})
                vram = bytearray()
                for offset in range(0, 0x4000, 0x0400):
                    part = request("tools/call", {"name": "read_memory", "arguments": {
                        "area": 8, "offset": f"{offset:04X}", "size": 0x0400}})
                    vram.extend(bytes.fromhex(json.loads(part["content"][0]["text"])["data"]))
                if len(vram) != 0x4000:
                    raise RuntimeError(f"Expected 16 KB VRAM, got {len(vram)} bytes")
                (report_dir / f"vram-reset-{args.hardware_frames}{suffix}.bin").write_bytes(vram)
                (report_dir / f"hardware-state-reset-{args.hardware_frames}{suffix}.json").write_text(
                    json.dumps({
                        "frames": args.hardware_frames,
                        "button": args.hardware_button,
                        "press_frame": args.hardware_press_frame if args.hardware_button else None,
                        "release_frame": release_frame if args.hardware_button else None,
                        "cartridge_sha256": source_hash,
                        "media": media_info,
                        "vdp_registers": json.loads(hardware_vdp_registers["content"][0]["text"]),
                        "psg_status": json.loads(hardware_psg_status["content"][0]["text"]),
                        "vram_sha256": hashlib.sha256(vram).hexdigest(),
                        "trace_count": len(lines),
                        "trace_last_sequence": sequence,
                    }, indent=2) + "\n", encoding="utf-8")
            ram = request("tools/call", {"name": "read_memory", "arguments": {"area": 7, "offset": "0000", "size": 32}})
            input_mode = request("tools/call", {"name": "read_memory", "arguments": {"area": 7, "offset": "007C", "size": 2}})
            shot = request("tools/call", {"name": "get_screenshot", "arguments": {}})
            screenshot_parts = [{"type": part.get("type"), "keys": list(part.keys()), "text_preview": part.get("text", "")[:200]} for part in shot.get("content", [])]
            for part in shot.get("content", []):
                if part.get("type") == "image" and part.get("data"):
                    (report_dir / "gearsystem-120.png").write_bytes(base64.b64decode(part["data"]))
            if args.button:
                tracing = request("tools/call", {"name": "set_trace_log", "arguments": {"enabled": True, "output": "memory", "memory_size": "100K", "filters": ["input.reads", "input.changes", "io.control"]}})
                if tracing.get("isError"):
                    raise RuntimeError(tracing.get("content"))
                pressed = request("tools/call", {"name": "controller_button", "arguments": {"player": 1, "button": args.button, "action": "press"}})
                request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": args.hold_frames, "mode": "sync"}})
                trace = request("tools/call", {"name": "get_trace_log", "arguments": {"count": 1000}})
                if trace.get("isError"):
                    raise RuntimeError(trace.get("content"))
                trace_data = json.loads(trace["content"][0]["text"])
                (report_dir / f"input-trace-{args.button}.json").write_text(json.dumps(trace_data, indent=2) + "\n", encoding="utf-8")
                request("tools/call", {"name": "set_trace_log", "arguments": {"enabled": False}})
                released = request("tools/call", {"name": "controller_button", "arguments": {"player": 1, "button": args.button, "action": "release"}})
                remaining_after_frames = args.after_frames
                while remaining_after_frames:
                    chunk = min(remaining_after_frames, 300)
                    request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": chunk, "mode": "sync"}})
                    remaining_after_frames -= chunk
                if args.late_button:
                    request("tools/call", {"name": "controller_button", "arguments": {"player": 1, "button": args.late_button, "action": "press"}})
                    remaining_late_hold = args.late_hold_frames
                    while remaining_late_hold:
                        chunk = min(remaining_late_hold, 300)
                        request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": chunk, "mode": "sync"}})
                        remaining_late_hold -= chunk
                    request("tools/call", {"name": "controller_button", "arguments": {"player": 1, "button": args.late_button, "action": "release"}})
                    remaining_late_after = args.late_after_frames
                    while remaining_late_after:
                        chunk = min(remaining_late_after, 300)
                        request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": chunk, "mode": "sync"}})
                        remaining_late_after -= chunk
                after = request("tools/call", {"name": "get_screenshot", "arguments": {}})
                after_ram = request("tools/call", {"name": "read_memory", "arguments": {"area": 7, "offset": "0000", "size": 1024}})
                after_ram_text = json.loads(after_ram["content"][0]["text"])["data"]
                after_ram_hash = hashlib.sha256(bytes.fromhex(after_ram_text)).hexdigest()
                for part in after.get("content", []):
                    if part.get("type") == "image" and part.get("data"):
                        (report_dir / f"gearsystem-after-{args.button}.png").write_bytes(base64.b64decode(part["data"]))
            else:
                pressed = released = None
                trace_data = None
                after_ram_hash = None
            if args.trace_cpu:
                request("tools/call", {"name": "set_trace_log", "arguments": {"enabled": True, "output": "memory", "memory_size": "5M", "filters": ["cpu.instructions"]}})
                request("tools/call", {"name": "debug_step_frame", "arguments": {"frames": 1, "mode": "sync"}})
                first_trace = request("tools/call", {"name": "get_trace_log", "arguments": {"start": 0, "count": 1000}})
                cpu_data = json.loads(first_trace["content"][0]["text"])
                lines = list(cpu_data["lines"])
                next_sequence = cpu_data["next_sequence"]
                while next_sequence < cpu_data["total_logged"]:
                    page = request("tools/call", {"name": "get_trace_log", "arguments": {"start": next_sequence, "count": 1000}})
                    parsed = json.loads(page["content"][0]["text"])
                    if parsed["next_sequence"] <= next_sequence:
                        raise RuntimeError("Trace pagination did not advance")
                    lines.extend(parsed["lines"])
                    next_sequence = parsed["next_sequence"]
                cpu_data["lines"] = lines
                cpu_data["count"] = len(lines)
                trace_name = f"cpu-trace-after-{args.button}-{args.after_frames}.json" if args.button else "cpu-trace-title.json"
                if args.late_button:
                    trace_name = f"cpu-trace-after-{args.button}-{args.after_frames}-late-{args.late_button}-{args.late_hold_frames}-{args.late_after_frames}.json"
                (report_dir / trace_name).write_text(json.dumps(cpu_data, indent=2) + "\n", encoding="utf-8")
            else:
                cpu_data = None
            if media.get("isError") or stepped.get("isError"):
                raise RuntimeError({"media": media.get("content"), "step": stepped.get("content")})
            print(json.dumps({
                "server": initialization.get("serverInfo"),
                "protocol": initialization.get("protocolVersion"),
                "tool_count": len(tools),
                "cartridge_sha256": source_hash,
                "media": media_info,
                "paused": paused.get("content"),
                "reset": reset.get("content"),
                "status": status.get("content"),
                "areas": areas.get("content"),
                "stepped": json.loads(stepped["content"][0]["text"]),
                "ram_preview": ram.get("content"),
                "input_mode_bytes": input_mode.get("content"),
                "screenshot_parts": screenshot_parts,
                "button": args.button,
                "hold_frames": args.hold_frames if args.button else None,
                "after_frames": args.after_frames if args.button else None,
                "late_button": args.late_button,
                "late_hold_frames": args.late_hold_frames if args.late_button else None,
                "late_after_frames": args.late_after_frames if args.late_button else None,
                "after_ram_sha256": after_ram_hash,
                "pressed": pressed.get("content") if pressed else None,
                "released": released.get("content") if released else None,
                "trace_summary": {"total_logged": trace_data.get("total_logged"), "count": trace_data.get("count"), "last_lines": trace_data.get("lines", [])[-20:]} if trace_data else None,
                "cpu_trace_summary": {"total_logged": cpu_data.get("total_logged"), "count": cpu_data.get("count"), "last_lines": cpu_data.get("lines", [])[-10:]} if cpu_data else None,
                "hardware_trace_summary": {"frames": hardware_trace_data["frames"],
                                           "count": hardware_trace_data["count"],
                                           "last_sequence": hardware_trace_data["last_sequence"]} if hardware_trace_data else None,
                "hardware_vdp_registers": hardware_vdp_registers.get("content") if hardware_vdp_registers else None,
                "hardware_psg_status": hardware_psg_status.get("content") if hardware_psg_status else None,
            }, indent=2))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Gearsystem smoke test failed: {error}", file=sys.stderr)
        sys.exit(1)
