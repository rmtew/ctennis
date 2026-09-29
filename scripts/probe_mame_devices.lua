for tag, device in pairs(manager.machine.devices) do
    print("DEVICE " .. tag .. " " .. device.name)
end
for tag, screen in pairs(manager.machine.screens) do
    print("SCREEN " .. tag)
end
