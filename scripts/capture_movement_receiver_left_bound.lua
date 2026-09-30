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
    {1512, "p2-left", 1},
    {1536, "p2-left", 0},
    {1536, "p2-right", 1},
    {1540, "p2-right", 0},
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
    return frame == 1541
end
