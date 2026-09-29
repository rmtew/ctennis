-- Independent MAME oracle: pre-counter-write RAM and ordered PSG writes.
local machine = manager.machine
local cpu = machine.devices[":z80"]
local program = cpu.spaces["program"]
local ports = cpu.spaces["io"]
local key = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local out = assert(io.open(assert(os.getenv("CT_TEST_CAPTURE")), "w"))
local frame = 0
local taps = {}
taps[1] = program:install_write_tap(0xC06B, 0xC06B, "regression-state", function(_, value)
    if frame < 1299 or frame > 1499 then return end
    local bytes = {}
    for address = 0xC000, 0xC0FF do
        bytes[#bytes + 1] = string.format("%02X", program:read_u8(address))
    end
    out:write(string.format("S\t%d\t%s\n", frame, table.concat(bytes)))
end)
taps[2] = ports:install_write_tap(0x7F, 0x7F, "regression-psg", function(_, value)
    if frame >= 1299 and frame <= 1499 then
        out:write(string.format("P\t%d\t%02X\n", frame, value))
    end
end)
emu.register_frame_done(function()
    assert(taps[1] and taps[2])
    if frame >= 1299 and frame <= 1499 then
        local bytes = {}
        for address = 0xC000, 0xC0FF do
            bytes[#bytes + 1] = string.format("%02X", program:read_u8(address))
        end
        out:write(string.format("T\t%d\t%s\n", frame, table.concat(bytes)))
    end
    frame = frame + 1
    if frame == 120 then key:set_value(1) end
    if frame == 420 then key:clear_value() end
    if frame == 1300 then button:set_value(1) end
    if frame == 1450 then button:clear_value() end
    if frame == 1500 then
        out:close()
        print("TEST_REFERENCE_COMPLETE")
    end
end)
