-- Diagnostic inventory of the SC-3000 input fields exposed by MAME.
local printed = false
emu.register_frame_done(function ()
    if printed then return end
    printed = true
    for tag, port in pairs(manager.machine.ioport.ports) do
        for name, field in pairs(port.fields) do
            print(string.format("INPUT %s %s mask=%X", tag, name, field.mask))
        end
    end
end)
