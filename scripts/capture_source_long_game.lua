-- Capture consecutive post-gameplay source RAM with port-1 fire held.
local machine = manager.machine
local program = machine.devices[":z80"].spaces["program"]
local screen = machine.screens[":screen"]
local key = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local run = assert(os.getenv("CT_LONG_RUN"))
assert(run:match("^[%w_-]+$"))
local last = assert(tonumber(os.getenv("CT_LONG_LAST")))
local out = assert(io.open("build/reference/source-long-game/" .. run .. ".tsv", "w"))
out:write("frame\ttick_written\tram\n")
local frame = 0
local count = 0
local tap = program:install_write_tap(0xC06B, 0xC06B, "long-game-checkpoint", function(_, value)
    if frame < 1299 or frame > last then return end
    local bytes = {}
    for address = 0xC000, 0xC0FF do
        bytes[#bytes + 1] = string.format("%02X", program:read_u8(address))
    end
    out:write(string.format("%d\t%02X\t%s\n", frame, value, table.concat(bytes)))
    count = count + 1
end)
emu.register_frame_done(function()
    assert(tap)
    frame = frame + 1
    if frame == 120 then key:set_value(1) end
    if frame == 420 then key:clear_value() end
    if frame == 1300 then button:set_value(1) end
    if frame == 2504 then
        assert(not screen:snapshot("long-game-after-award.png"))
    end
    if frame == 2557 then
        assert(not screen:snapshot("long-game-after-status.png"))
    end
    if frame == last + 1 then
        out:close()
        print(string.format("LONG_GAME_CAPTURE_COMPLETE %s %d", run, count))
    end
end)
