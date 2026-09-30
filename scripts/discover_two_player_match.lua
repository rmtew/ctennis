-- Source-only R2 schedule discovery; no gameplay state injection.
local exercise = dofile('scripts/calibrate_two_player_inputs.lua')
local restart = dofile('scripts/discover_one_player_restart.lua')
local p2 = manager.machine.ioport.ports[":ctrl2:mspad:JOYPAD"]:field(0x10)
local released_for_result = false
local restarted_action = false
return function(frame, ram, key, fire, emit)
    if frame <= 1844 then exercise(frame, ram, key, fire, emit) end
    if frame == 1850 then
        fire:set_value(1)
        p2:set_value(1)
        emit('REF CONTROL 1850 p1-button1 1')
        emit('REF CONTROL 1850 p2-button1 1')
    end
    if not released_for_result and ram:read_u8(0xC03D) & 0x40 ~= 0 then
        p2:clear_value()
        emit(string.format('REF CONTROL %d p2-button1 0', frame))
        released_for_result = true
    end
    if released_for_result and not restarted_action and ram:read_u8(0xC03D) & 4 == 0
            and ram:read_u16(0xC000) == 0x699 and ram:read_u8(0xC03A) & 0x40 ~= 0 then
        p2:set_value(1)
        emit(string.format('REF CONTROL %d p2-button1 1', frame))
        restarted_action = true
    end
    return restart(frame, ram, key, fire, emit)
end
