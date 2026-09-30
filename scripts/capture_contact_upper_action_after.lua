-- Frozen physical action pulse around source-accepted upper contact.
local changes = {
    {1300, "p1-left", 1},
    {1300, "p1-button1", 1},
    {1300, "p2-right", 1},
    {1301, "p1-button1", 0},
    {1348, "p2-right", 0},
    {1349, "p2-left", 1},
    {1452, "p1-left", 0},
    {1464, "p1-left", 1},
    {1600, "p1-button1", 1},
    {1601, "p1-left", 0},
    {1601, "p1-right", 1},
    {1601, "p1-button1", 0},
    {1643, "p2-left", 0},
    {1643, "p2-right", 1},
    {1694, "p2-right", 0},
    {1729, "p1-right", 0},
    {1799, "p1-left", 1},
    {1799, "p2-right", 1},
    {1935, "p1-button1", 1},
    {1936, "p1-button1", 0},
    {1983, "p2-left", 1},
    {1983, "p2-right", 0},
    {2007, "p2-button1", 1},
    {2011, "p2-button1", 0},
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
    return frame == 2021
end
