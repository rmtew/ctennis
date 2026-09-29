-- One-player movement: frame samples plus writes to the candidate X byte.
local machine = manager.machine
local cpu_device = machine.devices[":z80"]
local cpu = cpu_device.spaces["program"]
local pc = cpu_device.state["PC"]
local ins = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local joy = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]
local left = joy:field(0x04)
local frames = 0
local file = assert(io.open("build/mame/player-left-trace.tsv", "w"))
file:write("event\tframe\tpc\taddress\tvalue\tc021\tc035\tc04a\tc04e\tc03d\tjoy\n")

local function row(event, address, value)
    file:write(string.format("%s\t%d\t%04X\t%04X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\t%02X\n",
        event, frames, pc.value, address, value, cpu:read_u8(0xC021),
        cpu:read_u8(0xC035), cpu:read_u8(0xC04A), cpu:read_u8(0xC04E),
        cpu:read_u8(0xC03D), joy:read()))
end

local taps = {}
for _, address in ipairs({0xC021, 0xC035, 0xC04A, 0xC04E, 0xC06B}) do
    taps[#taps + 1] = cpu:install_write_tap(address, address, "player-x", function (written, value, mask)
        if frames >= 1280 and frames <= 1500 then row("write", written, value) end
    end)
end

emu.register_frame_done(function ()
    assert(#taps == 5)
    frames = frames + 1
    if frames == 120 then ins:set_value(1) end
    if frames == 420 then ins:clear_value() end
    if frames == 1300 then left:set_value(1) end
    if frames == 1450 then left:clear_value() end
    if frames >= 1280 and frames <= 1500 then row("frame", 0, 0) end
    if frames == 1500 then
        file:close()
        print("TRACE_COMPLETE build/mame/player-left-trace.tsv")
    end
end)
