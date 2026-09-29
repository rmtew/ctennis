-- Deterministic SC-3000 title-key probe. Run with CT_CASE=none|ins|func.
local case = os.getenv("CT_CASE") or "none"
local release_frame = tonumber(os.getenv("CT_RELEASE_FRAME")) or 150
local p1_input = os.getenv("CT_P1_INPUT") or (os.getenv("CT_SERVE") == "1" and "button1" or "none")
local long_run = os.getenv("CT_LONG") == "1"
local p1_press_frame = tonumber(os.getenv("CT_P1_PRESS_FRAME")) or 620
local p1_release_frame = tonumber(os.getenv("CT_P1_RELEASE_FRAME")) or 740
local input_mask = ({none = nil, button1 = 0x10, button2 = 0x20,
                     left = 0x04, right = 0x08, up = 0x01, down = 0x02})[p1_input]
assert(p1_input == "none" or input_mask)
assert(case == "none" or case == "ins" or case == "func")
local key
if case == "ins" then
    key = manager.machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
elseif case == "func" then
    key = manager.machine.ioport.ports[":sgexp:sk1100:PB5"]:field(0x08)
end
local cpu = manager.machine.devices[":z80"].spaces["program"]
local pc = manager.machine.devices[":z80"].state["PC"]
local screen = manager.machine.screens[":screen"]
local p1_key = input_mask and manager.machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(input_mask) or nil
assert(cpu and screen)
local frames = 0

local function capture()
    local stem = string.format("%s-%s-f%03d", case, p1_input, frames)
    local bytes = {}
    for address = 0xC000, 0xC3FF do
        bytes[#bytes + 1] = string.char(cpu:read_u8(address))
    end
    local file = assert(io.open("build/mame/captures/" .. stem .. ".ram", "wb"))
    file:write(table.concat(bytes))
    file:close()
    local error = screen:snapshot(stem .. ".png")
    assert(not error, tostring(error))
    print(string.format("CAPTURE %s PC=%04X C03D=%02X C06C=%02X C07C=%02X C053=%02X C056=%02X",
        stem, pc.value,
        cpu:read_u8(0xC03D), cpu:read_u8(0xC06C), cpu:read_u8(0xC07C),
        cpu:read_u8(0xC053), cpu:read_u8(0xC056)))
end

emu.register_frame_done(function ()
    frames = frames + 1
    if key and frames == 120 then
        key:set_value(1)
        print("KEY_PRESS " .. case)
    elseif key and frames == release_frame then
        key:clear_value()
        print("KEY_RELEASE " .. case)
    end
    if p1_key and frames == p1_press_frame then
        p1_key:set_value(1)
        print("P1_PRESS " .. p1_input)
    elseif p1_key and frames == p1_release_frame then
        p1_key:clear_value()
        print("P1_RELEASE " .. p1_input)
    end
    if frames == 120 or frames == 180 or frames == 300 or frames == 450 or frames == 600 or
       (frames == 660 or (p1_key and (frames == 900 or frames == 1200 or frames == 1500)) or
        (long_run and (frames == 900 or frames == 1200 or frames == 1500 or frames == 1800 or
                       frames == 2400 or frames == 3000))) then
        capture()
    end
end)
