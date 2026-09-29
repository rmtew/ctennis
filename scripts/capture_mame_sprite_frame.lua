-- Capture a controlled active-play frame and full VDP RAM for sprite validation.
local machine = manager.machine
local ram = machine.devices[":z80"].spaces["program"]
local ports = machine.devices[":z80"].spaces["io"]
local vram = machine.devices[":tms9918a"].spaces["vram"]
local screen = machine.screens[":screen"]
local key = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
assert(ram and vram and screen and key)
local frames = 0
local previous_control = nil
local register_writes = {}
local control_tap = ports:install_write_tap(0xBF, 0xBF, "sprite-vdp-registers", function(_, value)
    if value >= 0x80 and value <= 0x87 then
        register_writes[#register_writes + 1] = string.format("%d %d %02X", frames, value - 0x80, previous_control or 0)
    end
    previous_control = value
end)

local function write_space(path, space, first, last)
    local chunks = {}
    for address = first, last do chunks[#chunks + 1] = string.char(space:read_u8(address)) end
    local file = assert(io.open(path, "wb"))
    file:write(table.concat(chunks))
    file:close()
end

emu.register_frame_done(function()
    frames = frames + 1
    if frames == 120 then key:set_value(1) end
    if frames == 420 then key:clear_value() end
    if frames == 1310 then
        assert(control_tap)
        write_space("build/reference/source-timing/sprite-f1310.ram", ram, 0xC000, 0xC3FF)
        write_space("build/reference/source-timing/sprite-f1310.vram", vram, 0, 0x3FFF)
        local file = assert(io.open("build/reference/source-timing/sprite-f1310-registers.txt", "w"))
        file:write(table.concat(register_writes, "\n"), "\n")
        file:close()
        assert(not screen:snapshot("sprite-f1310.png"))
        print("SPRITE_CAPTURE_COMPLETE 1310")
    end
end)
