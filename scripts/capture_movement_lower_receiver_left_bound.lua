-- Frozen from source-only two-player match discovery; no state-dependent input.
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
    {1820, "p1-right", 1},
    {1820, "p2-left", 1},
    {1844, "p1-right", 0},
    {1844, "p2-left", 0},
    {1850, "p1-button1", 1},
    {1850, "p2-button1", 1},
    {6153, "p2-left", 1},
    {6173, "p2-left", 0},
    {6173, "p2-right", 1},
    {6177, "p2-right", 0},
}
local ports = manager.machine.ioport.ports
local masks = {up=1, down=2, left=4, right=8, button1=16, button2=32}
return function(frame, ram, key, fire, emit)
    for _, change in ipairs(changes) do
        if change[1] == frame then
            local player, action = change[2]:match("p(%d)%-(.+)")
            local field = change[2] == "select" and key or change[2] == "fire" and fire
            if player then field = ports[":ctrl" .. player .. ":mspad:JOYPAD"]:field(masks[action]) end
            assert(field)
            if change[3] == 1 then field:set_value(1) else field:clear_value() end
            emit(string.format("REF CONTROL %d %s %d", frame, change[2], change[3]))
        end
    end
    return frame == 6178
end
