-- First one-player point: frame samples and writes along the ball/score path.
local machine = manager.machine
local device = machine.devices[":z80"]
local cpu = device.spaces["program"]
local pc = device.state["PC"]
local screen = machine.screens[":screen"]
local ins = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local frames = 0
local file = assert(io.open("build/mame/ball-point-trace.tsv", "w"))
local fields = {0xC038, 0xC039, 0xC03A, 0xC03D, 0xC03E, 0xC03F,
                0xC034, 0xC035, 0xC04A, 0xC04D, 0xC04E,
                0xC057, 0xC058, 0xC059, 0xC05A, 0xC05B, 0xC05C,
                0xC060, 0xC061, 0xC062, 0xC063, 0xC064, 0xC065,
                0xC066, 0xC06C}
file:write("event\tframe\tpc\taddress\tvalue")
for _, address in ipairs(fields) do file:write(string.format("\tc%03x", address - 0xC000)) end
file:write("\n")

local function row(event, address, value)
    file:write(string.format("%s\t%d\t%04X\t%04X\t%02X", event, frames, pc.value, address, value))
    for _, field in ipairs(fields) do file:write(string.format("\t%02X", cpu:read_u8(field))) end
    file:write("\n")
end

local taps = {}
for _, address in ipairs({0xC034, 0xC035, 0xC039, 0xC03A, 0xC03F,
                         0xC04D, 0xC04E, 0xC060, 0xC061, 0xC066}) do
    taps[#taps + 1] = cpu:install_write_tap(address, address, "ball-point", function(written, value)
        if frames >= 1250 and frames <= 1500 then row("write", written, value) end
    end)
end

emu.register_frame_done(function()
    assert(#taps == 10)
    frames = frames + 1
    if frames == 120 then ins:set_value(1) end
    if frames == 420 then ins:clear_value() end
    if frames == 1300 then button:set_value(1) end
    if frames == 1450 then button:clear_value() end
    if frames >= 1250 and frames <= 1500 then row("frame", 0, 0) end
    if frames == 1317 or frames == 1363 or frames == 1369 or
       frames == 1412 or frames == 1434 then
        assert(not screen:snapshot(string.format("ball-point-f%04d.png", frames)))
    end
    if frames == 1500 then
        file:close()
        print("TRACE_COMPLETE build/mame/ball-point-trace.tsv")
    end
end)
