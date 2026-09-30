-- Source-only input discovery. Freeze the emitted control events for acceptance.
local phase = "match"
local release_frame
return function(frame, ram, key, fire, emit)
    local mode = ram:read_u8(0xC03D)
    if phase == "match" and mode & 0x40 ~= 0 then
        fire:clear_value()
        emit(string.format("REF CONTROL %d fire 0", frame))
        print("MATCH_AWARD " .. frame)
        phase = "result"
    elseif phase == "result" and mode & 4 ~= 0 then
        key:set_value(1)
        emit(string.format("REF CONTROL %d select 1", frame))
        print("RESTART_SELECTION " .. frame)
        release_frame = frame + 300
        phase = "selection"
    elseif phase == "selection" and frame == release_frame then
        key:clear_value()
        emit(string.format("REF CONTROL %d select 0", frame))
        phase = "serve-wait"
    elseif phase == "serve-wait" and mode & 4 == 0 and ram:read_u16(0xC000) == 0x699
            and ram:read_u8(0xC03A) & 0x40 ~= 0 then
        fire:set_value(1)
        emit(string.format("REF CONTROL %d fire 1", frame))
        print("RESTART_FIRE " .. frame)
        phase = "serve"
    elseif phase == "serve" and ram:read_u8(0xC038) & 0x40 ~= 0
            and ram:read_u8(0xC066) > 0 then
        print("RESTART_SERVE_FLIGHT " .. frame)
        return true
    end
    return false
end
