-- Replay the established physical R2 prefix, then hold alternate serve limits.
-- No game-state writes or synthetic animation flags.
local changes = {
    {1320, "p1-up", 1},
    {1344, "p1-up", 0},
    {1360, "p1-down", 1},
    {1384, "p1-down", 0},
    {1400, "p1-left", 1},
    {1424, "p1-left", 0},
    {1440, "p1-right", 1},
    {1464, "p1-right", 0},
    {1480, "p1-button1", 1},
    {1504, "p1-button1", 0},
    {1520, "p1-button2", 1},
    {1544, "p1-button2", 0},
    {1560, "p2-up", 1},
    {1584, "p2-up", 0},
    {1600, "p2-down", 1},
    {1624, "p2-down", 0},
    {1640, "p2-left", 1},
    {1664, "p2-left", 0},
    {1680, "p2-right", 1},
    {1704, "p2-right", 0},
    {1720, "p2-button1", 1},
    {1744, "p2-button1", 0},
    {1760, "p2-button2", 1},
    {1784, "p2-button2", 0},
    {1900, "p1-down", 1},
    {1900, "p2-down", 1},
    {2004, "p1-down", 0},
    {2004, "p2-down", 0},
    {2020, "p1-up", 1},
    {2020, "p2-up", 1},
    {2124, "p1-up", 0},
    {2124, "p2-up", 0},
    {2140, "p1-down", 1},
    {2140, "p2-down", 1},
    {2244, "p1-down", 0},
    {2244, "p2-down", 0},
    {2260, "p1-left", 1},
    {2260, "p2-left", 1},
    {2364, "p1-left", 0},
    {2364, "p2-left", 0},
    {2380, "p1-right", 1},
    {2380, "p2-right", 1},
    {2484, "p1-right", 0},
    {2484, "p2-right", 0},
    {2500, "p1-left", 1},
    {2500, "p2-left", 1},
    {2604, "p1-left", 0},
    {2604, "p2-left", 0},
}
local ports = manager.machine.ioport.ports
local masks = {up=1, down=2, left=4, right=8, button1=16, button2=32}
return function(frame, ram, key, fire, emit)
    for _, change in ipairs(changes) do
        if change[1] == frame then
            local player, action = change[2]:match("p(%d)%-(.+)")
            local field = assert(ports[":ctrl" .. player .. ":mspad:JOYPAD"]:field(masks[action]))
            if change[3] == 1 then field:set_value(1) else field:clear_value() end
            emit(string.format("REF CONTROL %d %s %d", frame, change[2], change[3]))
        end
    end
    return frame == 2621
end
