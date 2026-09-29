-- Verify that MAME's SC-3000 keyboard fields accept scripted presses.
local frames = 0
local row = manager.machine.ioport.ports[":sgexp:sk1100:PA3"]
local key = row:field(0x10) -- Del/Ins
emu.register_frame_done(function ()
    frames = frames + 1
    if frames == 30 then
        key:set_value(1)
        print(string.format("INS_PRESS_REQUEST frame=%d row=%02X", frames, row:read()))
    elseif frames == 31 then
        print(string.format("INS_PRESSED frame=%d row=%02X", frames, row:read()))
    elseif frames == 60 then
        key:clear_value()
        print(string.format("INS_RELEASE_REQUEST frame=%d row=%02X", frames, row:read()))
    elseif frames == 61 then
        print(string.format("INS_RELEASED frame=%d row=%02X", frames, row:read()))
    end
end)
