-- Frozen source-only schedule discovered with discover_one_player_restart.lua.
-- Never consult port state or modify source RAM.
local changes = {
    [13260] = {"fire", 0},
    [13835] = {"select", 1},
    [14135] = {"select", 0},
    [14660] = {"fire", 1},
}
return function(frame, ram, key, fire, emit)
    local change = changes[frame]
    if change then
        local field = change[1] == "select" and key or fire
        if change[2] == 1 then field:set_value(1) else field:clear_value() end
        emit(string.format("REF CONTROL %d %s %d", frame, change[1], change[2]))
    end
    return frame == 14678
end
