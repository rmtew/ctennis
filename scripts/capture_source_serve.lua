-- Capture a deterministic one-player serve from the pre-serve state.
local machine = manager.machine
local program = machine.devices[":z80"].spaces["program"]
local key = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local run = assert(os.getenv("CT_SERVE_RUN"))
assert(run:match("^[%w_-]+$"))
local out = assert(io.open("build/reference/source-serve/" .. run .. ".tsv", "w"))
out:write("frame\ttick_written\tram\n")
local frame = 0
local tap = program:install_write_tap(0xC06B, 0xC06B, "serve-checkpoint", function(_, value)
    if frame < 1299 or frame > 1500 then return end
    local bytes = {}
    for address = 0xC000, 0xC0FF do
        bytes[#bytes + 1] = string.format("%02X", program:read_u8(address))
    end
    out:write(string.format("%d\t%02X\t%s\n", frame, value, table.concat(bytes)))
end)
emu.register_frame_done(function()
    assert(tap)
    frame = frame + 1
    if frame == 120 then key:set_value(1) end
    if frame == 420 then key:clear_value() end
    if frame == 1300 then button:set_value(1) end
    if frame == 1450 then button:clear_value() end
    if frame == 1500 then
        out:close()
        print("SERVE_CAPTURE_COMPLETE " .. run)
    end
end)
