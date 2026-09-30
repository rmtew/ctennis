-- Physical input calibration. Observe source state; never write cartridge RAM.
local ports = manager.machine.ioport.ports
local names = {"up", "down", "left", "right", "button1", "button2"}
local masks = {1, 2, 4, 8, 16, 32}
local fields = {}
for player = 1, 2 do
    for index, mask in ipairs(masks) do
        fields[#fields + 1] = {field = assert(ports[string.format(":ctrl%d:mspad:JOYPAD", player)]:field(mask)),
                              name = string.format("p%d-%s", player, names[index])}
    end
end
return function(frame, ram, key, fire, emit)
    for index, item in ipairs(fields) do
        local start = 1320 + (index - 1) * 40
        if frame == start then
            item.field:set_value(1)
            emit(string.format("REF CONTROL %d %s 1", frame, item.name))
        elseif frame == start + 24 then
            item.field:clear_value()
            emit(string.format("REF CONTROL %d %s 0", frame, item.name))
        end
    end
    if frame == 1820 or frame == 1844 then
        local value = frame == 1820 and 1 or 0
        for _, index in ipairs({4, 9}) do
            if value == 1 then fields[index].field:set_value(1) else fields[index].field:clear_value() end
            emit(string.format("REF CONTROL %d %s %d", frame, fields[index].name, value))
        end
    end
    return frame == 1860
end
