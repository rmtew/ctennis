-- Reproduce original-cartridge ball/shadow frames from the retained serve run.
local machine = manager.machine
local screen = machine.screens[":screen"]
local key = machine.ioport.ports[":sgexp:sk1100:PA3"]:field(0x10)
local button = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x10)
local left = machine.ioport.ports[":ctrl1:mspad:JOYPAD"]:field(0x04)
local scenario = os.getenv("CT_BALL_SHADOW_SCENARIO") or "serve"
assert(scenario == "serve" or scenario == "wait")
local targets = scenario == "serve"
    and {[1350] = true, [1361] = true, [1390] = true, [1411] = true}
    or {[1310] = true, [1320] = true}
local frame = 0
emu.register_frame_done(function()
    frame = frame + 1
    if frame == 120 then key:set_value(1) end
    if frame == 420 then key:clear_value() end
    if scenario == "serve" then
        if frame == 1300 then button:set_value(1) end
        if frame == 1450 then button:clear_value() end
    else
        if frame == 1300 then left:set_value(1) end
        if frame == 1320 then left:clear_value() end
    end
    if targets[frame] then
        assert(not screen:snapshot(string.format("ball-shadow-%s-%04d.png", scenario, frame)))
        print("BALL_SHADOW_CAPTURE " .. scenario .. " " .. frame)
    end
end)
