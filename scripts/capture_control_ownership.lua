-- CT-03: reach the first exchanged-end serve through the existing source
-- schedule, then a bounded movement/reversal/action window. No RAM writes.
local previous = dofile('scripts/capture_two_player_match.lua')
local ports = manager.machine.ioport.ports
local controls = {'right', 'left', 'button1', 'button2'}
local masks = {right=8, left=4, button1=16, button2=32}
local start = nil
local function set(frame, player, action, held, emit)
    local field = ports[':ctrl' .. player .. ':mspad:JOYPAD']:field(masks[action])
    if held then field:set_value(1) else field:clear_value() end
    emit(string.format('REF CONTROL %d p%d-%s %d', frame, player, action, held and 1 or 0))
end
return function(frame, ram, key, fire, emit)
    if not start then
        previous(frame, ram, key, fire, emit)
        if ram:read_u8(0xc03d) & 0x10 ~= 0 and ram:read_u8(0xc03a) == 0x40 then
            start = frame
            for p=1,2 do
                for _,action in ipairs(controls) do set(frame,p,action,false,emit) end
            end
        end
    else
        local elapsed = frame-start
        local events = {
            [8]={{1,'left',true},{2,'right',true}},
            [24]={{1,'left',false},{2,'right',false}},
            [32]={{1,'right',true},{2,'left',true}},
            [48]={{1,'right',false},{2,'left',false}},
            [56]={{2,'button2',true}}, [72]={{2,'button2',false}},
            [80]={{1,'button1',true}}, [96]={{1,'button1',false}},
        }
        for _,event in ipairs(events[elapsed] or {}) do set(frame,event[1],event[2],event[3],emit) end
        if elapsed == 104 then return true end
    end
    return false
end
