-- Frozen physical controls only; no cartridge RAM writes.
local changes = {
    {1320, "p1-down", 1},
    {1320, "p2-down", 1},
    {1424, "p1-down", 0},
    {1424, "p2-down", 0},
    {1440, "p1-up", 1},
    {1440, "p2-up", 1},
    {1544, "p1-up", 0},
    {1544, "p2-up", 0},
    {1560, "p1-down", 1},
    {1560, "p2-down", 1},
    {1664, "p1-down", 0},
    {1664, "p2-down", 0},
    {1680, "p1-right", 1},
    {1680, "p2-right", 1},
    {1784, "p1-right", 0},
    {1784, "p2-right", 0},
    {1800, "p1-left", 1},
    {1800, "p2-left", 1},
    {1904, "p1-left", 0},
    {1904, "p2-left", 0},
    {1920, "p1-right", 1},
    {1920, "p2-right", 1},
    {2024, "p1-right", 0},
    {2024, "p2-right", 0},
}
local ports = manager.machine.ioport.ports
local masks = {up=1, down=2, left=4, right=8}
return function(frame, ram, key, fire, emit)
    for _, change in ipairs(changes) do
        if change[1] == frame then
            local player, action = change[2]:match("p(%d)%-(.+)")
            local field = assert(ports[":ctrl" .. player .. ":mspad:JOYPAD"]:field(masks[action]))
            if change[3] == 1 then field:set_value(1) else field:clear_value() end
            emit(string.format("REF CONTROL %d %s %d", frame, change[2], change[3]))
        end
    end
    return frame == 2041
end
