-- Exact instruction boundaries via synchronous debugger actions; no stepping.
-- Use -debug -debugger none. Actions print observations and immediately resume.
local machine = manager.machine
local cpu = machine.devices[":z80"]
local program = cpu.spaces["program"]
local ports = cpu.spaces["io"]
local dbg = assert(machine.debugger)
local two_player = os.getenv("CT_TEST_SELECT") == "two"
local key = two_player and machine.ioport.ports[":sgexp:sk1100:PB5"]:field(0x08)
    or machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local out = assert(io.open(assert(os.getenv("CT_TEST_CAPTURE")), "w"))
local frame, ordinal, sequence = 0, -1, 0
local active, finished = false, false
local taps = {}
local last_frame = tonumber(os.getenv("CT_TEST_LAST_FRAME") or "3000")
local condition = string.format("temp8 >= 0x%x && temp8 <= 0x%x", 1298, last_frame)
local policy_path = os.getenv("CT_TEST_POLICY")
local policy = policy_path and dofile(policy_path) or nil
local stop_requested = false

local function emit(line)
    if finished then return end
    sequence = sequence + 1
    out:write(string.format("%d\t%s\n", sequence, line))
end

local function drain()
    if #dbg.consolelog == 0 then return end
    for _, line in ipairs(dbg.consolelog) do
        if line:sub(1, 4) == "REF " then
            if line:sub(1, 6) == "REF B " then
                ordinal = tonumber(line:match("^REF B (%d+)"))
                active = true
            elseif line:sub(1, 6) == "REF E " then
                active = false
            end
            emit(line)
        end
    end
    -- Avoid the debugger's bounded console history losing old records.
    dbg:command("cls")
end

local function snapshot(kind, advance)
    local commands = {}
    if advance then
        commands[#commands + 1] = "do temp9=temp9+1"
        commands[#commands + 1] = "do temp7=1"
    end
    commands[#commands + 1] = string.format(
        'printf "REF %s %%d %%d %%04X %%04X",temp9,temp8,pc,hl', kind)
    for offset = 0, 255, 64 do
        local args = {}
        for address = 0xC000 + offset, 0xC000 + offset + 63, 8 do
            args[#args + 1] = string.format("q@%04x", address)
        end
        commands[#commands + 1] = string.format('printf "REF D %d %s",%s',
            offset, string.rep("%016X", 8), table.concat(args, ","))
    end
    if kind == "E" then commands[#commands + 1] = "do temp7=0" end
    commands[#commands + 1] = "g"
    return table.concat(commands, ";")
end

dbg:command("do temp8=0")
dbg:command("do temp9=-1")
dbg:command("do temp7=0")
local begin_bp = cpu.debug:bpset(0x0049, condition, snapshot("B", true))
cpu.debug:bpset(0x06B1, "temp7 == 1", snapshot("T", false))
cpu.debug:bpset(0x0045, "temp7 == 1", snapshot("E", false))
-- Observe normalized input results at RET, and the actual R value consumed by
-- LD A,R before its BIT test. Neither hook changes CPU state or random choices.
for _, item in ipairs({{0x0886, "I0"}, {0x088F, "I1"}, {0x0DBB, "R"}}) do
    cpu.debug:bpset(item[1], "temp7 == 1", string.format(
        'printf "REF %s %%d %%d %%04X %%02X",temp9,temp8,pc,a;g', item[2]))
end
-- Single-entry markers, not busy-wait loop breakpoints.
for _, address in ipairs({0x0109, 0x01D3, 0x0144, 0x025D, 0x0211, 0x011C, 0x0580, 0x058F}) do
    cpu.debug:bpset(address, condition, string.format(
        'printf "REF M %%d %%d %%04X",temp9,temp8,%04x;g', address))
end

if os.getenv("CT_TEST_CONTACT_MARKERS") == "1" then
    for _, address in ipairs({0x0C9F, 0x0FD3}) do
        cpu.debug:bpset(address, "temp7 == 1", string.format(
            'printf "REF M %%d %%d %%04X",temp9,temp8,%04x;g', address))
    end
end

taps[1] = ports:install_write_tap(0x7F, 0x7F, "round-psg", function(_, value)
    if frame < 1298 or finished then return end
    drain()
    emit(string.format("REF P %d %d %04X %02X", ordinal, frame, cpu.state["CURPC"].value, value))
end)
taps[2] = program:install_write_tap(0xC000, 0xC0FF, "round-between-writes", function(address, value)
    if frame < 1298 or finished then return end
    drain()
    if not active then
        emit(string.format("REF W %d %d %04X %04X %02X %02X", ordinal, frame,
            cpu.state["CURPC"].value, address, program:read_u8(address), value))
    end
end)

emu.register_frame_done(function()
    if finished then return end
    assert(taps[1] and taps[2])
    drain()
    frame = frame + 1
    -- Always prefix numbers: an unprefixed AF2 is a register name, not 0xAF2.
    dbg:command(string.format("do temp8=0x%x", frame))
    if frame == 120 then
        key:set_value(1)
    elseif frame == 420 then
        key:clear_value()
    elseif frame == 1300 and os.getenv("CT_TEST_FIRE") ~= "0" then
        button:set_value(1)
        emit("REF CONTROL 1300 fire 1")
    end
    if not stop_requested and policy and policy(frame, program, key, button, emit) then
        stop_requested = true
        cpu.debug:bpdisable(begin_bp)
    end
    if (stop_requested and not active) or frame == last_frame + 2 then
        finished = true
        out:close()
        print("ROUND_REFERENCE_COMPLETE")
    end
end)
dbg.execution_state = "run"
