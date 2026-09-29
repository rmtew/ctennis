-- Capture gameplay update cadence and input visibility on MAME SC-3000.
-- CT_RUN selects an ignored build/reference/source-timing/<run>.tsv output.
local machine = manager.machine
local device = machine.devices[":z80"]
local program = device.spaces["program"]
local ports = device.spaces["io"]
local pc = device.state["PC"]
local select_one_player = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local joystick = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]
local left = joystick:field(0x04)
local run = os.getenv("CT_RUN") or "probe"
assert(run:match("^[%w_-]+$"))
assert(program and ports and pc and select_one_player and left)

local output = assert(io.open("build/reference/source-timing/" .. run .. ".tsv", "w"))
output:write("event\tframe\tpc\taddress\tvalue\tjoy\tmode\tinput_a\tinput_b\tlower_x\ttick\tram\n")
local frames = 0
local first = 1280
local last = 1340
local taps = {}

local function ram_hex()
    local parts = {}
    for address = 0xC000, 0xC3FF do
        parts[#parts + 1] = string.format("%02X", program:read_u8(address))
    end
    return table.concat(parts)
end

local function record(event, address, value, with_ram)
    if frames < first or frames > last then return end
    output:write(string.format("%s\t%d\t%04X\t%04X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\t%s\n",
        event, frames, pc.value, address, value, joystick:read(),
        program:read_u8(0xC03D), program:read_u8(0xC053),
        program:read_u8(0xC056), program:read_u8(0xC04A),
        program:read_u8(0xC06B), with_ram and ram_hex() or ""))
end

-- C06B is written at 06B1 after gameplay phases and before the audio/VDP tail.
taps[#taps + 1] = program:install_write_tap(0xC06B, 0xC06B, "gameplay-checkpoint", function(address, value)
    record("checkpoint", address, value, true)
end)
for _, address in ipairs({0xC053, 0xC056, 0xC04A}) do
    taps[#taps + 1] = program:install_write_tap(address, address, "input-and-move", function(written, value)
        record("write", written, value, false)
    end)
end
for _, address in ipairs({0xDC, 0xDD}) do
    taps[#taps + 1] = ports:install_read_tap(address, address, "input-port", function(read_address, value)
        record("port", read_address, value, false)
    end)
end

emu.register_frame_done(function()
    assert(#taps == 6)
    frames = frames + 1
    if frames == 120 then select_one_player:set_value(1) end
    if frames == 420 then select_one_player:clear_value() end
    if frames == 1300 then left:set_value(1) end
    if frames == 1320 then left:clear_value() end
    if frames >= first and frames <= last then record("frame_done", 0, 0, false) end
    if frames == last then
        output:close()
        print("TIMING_CAPTURE_COMPLETE " .. run)
    end
end)
