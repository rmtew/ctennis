-- Controlled one-player serve/point: record candidate score and state writes.
local machine = manager.machine
local device = machine.devices[":z80"]
local cpu = device.spaces["program"]
local pc = device.state["PC"]
local ins = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local frames = 0
local file = assert(io.open("build/mame/score-point-trace.tsv", "w"))
file:write("event\tframe\tpc\taddress\tvalue\tc03d\tc03e\tc03f\tc040\tc041\tc042\tc043\tc044\n")

local function row(event, address, value)
    file:write(string.format("%s\t%d\t%04X\t%04X\t%02X", event, frames, pc.value, address, value))
    for offset = 0x3D, 0x44 do
        file:write(string.format("\t%02X", cpu:read_u8(0xC000 + offset)))
    end
    file:write("\n")
end

local taps = {}
for _, address in ipairs({0xC03D, 0xC03E, 0xC03F, 0xC040, 0xC041, 0xC042, 0xC043, 0xC044}) do
    taps[#taps + 1] = cpu:install_write_tap(address, address, "score-state", function(written, value)
        if frames >= 1200 and frames <= 1800 then row("write", written, value) end
    end)
end

emu.register_frame_done(function()
    assert(#taps == 8)
    frames = frames + 1
    if frames == 120 then ins:set_value(1) end
    if frames == 420 then ins:clear_value() end
    if frames == 1300 then button:set_value(1) end
    if frames == 1450 then button:clear_value() end
    if frames >= 1200 and frames <= 1800 then row("frame", 0, 0) end
    if frames == 1800 then
        file:close()
        print("TRACE_COMPLETE build/mame/score-point-trace.tsv")
    end
end)
