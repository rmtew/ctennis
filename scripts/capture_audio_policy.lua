-- Read-only sound observation alongside an already frozen physical input policy.
local base = dofile(assert(os.getenv("CT_AUDIO_BASE_POLICY")))
local machine = manager.machine
local cpu = machine.devices[":z80"]
local ports = cpu.spaces["io"]
local file = assert(io.open(assert(os.getenv("CT_AUDIO_EVENTS")), "w"))
local frames = assert(io.open(assert(os.getenv("CT_AUDIO_FRAMES")), "w"))
local frame = 0
file:write("seconds\tattoseconds\tframe\tpc\tvalue\n")
frames:write("seconds\tattoseconds\tframe\n")
local tap = ports:install_write_tap(0x7F, 0x7F, "audio-reference", function(_, value)
    local time = machine.time
    file:write(string.format("%d\t%d\t%d\t%04X\t%02X\n", time.seconds,
        time.attoseconds, frame, cpu.state["CURPC"].value, value))
    file:flush()
end)
return function(next_frame, ram, key, fire, emit)
    assert(tap)
    frame = next_frame
    local time = machine.time
    frames:write(string.format("%d\t%d\t%d\n", time.seconds, time.attoseconds, frame))
    frames:flush()
    return base(next_frame, ram, key, fire, emit)
end
