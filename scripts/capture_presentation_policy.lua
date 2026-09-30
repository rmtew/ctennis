-- Observe the frozen source replay without writing CPU/game state.
local base = dofile(assert(os.getenv("CT_MEDIA_BASE_POLICY")))
local targets = dofile(assert(os.getenv("CT_MEDIA_TARGETS")))
local machine = manager.machine
local cpu = machine.devices[":z80"]
local ports = cpu.spaces["io"]
local vram = machine.devices[":tms9918a"].spaces["vram"]
local screen = machine.screens[":screen"]
local directory = assert(os.getenv("CT_MEDIA_DIRECTORY"))
local registers, latch, taps = {}, nil, {}
-- BF is a two-byte control port. A status read cancels an incomplete pair.
taps[1] = ports:install_write_tap(0xBF, 0xBF, "media-control", function(_, value)
    if latch == nil then
        latch = value
    else
        if value >= 0x80 and value <= 0x87 then registers[value - 0x80] = latch end
        latch = nil
    end
end)
taps[2] = ports:install_read_tap(0xBF, 0xBF, "media-status", function() latch = nil end)
local function dump(path, space, first, last)
    local file = assert(io.open(path, "wb"))
    for address = first, last do file:write(string.char(space:read_u8(address))) end
    file:close()
end
return function(frame, ram, key, fire, emit)
    local stop = base(frame, ram, key, fire, emit)
    if targets[frame] then
        assert(taps[1] and taps[2])
        local stem = string.format("f%05d", frame)
        screen:snapshot(stem .. ".png")
        dump(directory .. "/" .. stem .. ".ram", ram, 0xC000, 0xC3FF)
        dump(directory .. "/" .. stem .. ".vram", vram, 0, 0x3FFF)
        local file = assert(io.open(directory .. "/" .. stem .. ".regs", "wb"))
        for index = 0, 7 do
            local value = assert(registers[index], "VDP register not observed")
            file:write(string.char(value))
        end
        file:close()
        file = assert(io.open(directory .. "/" .. stem .. ".pc", "w"))
        file:write(string.format("%04X\n", cpu.state["CURPC"].value))
        file:close()
    end
    return stop
end
