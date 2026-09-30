-- Bounded CT-02 original media: title/pre-choice and first stable chosen court.
-- Inputs only; never writes source CPU/game RAM.
local machine=manager.machine
local cpu=machine.devices[":z80"]
local ram=cpu.spaces["program"]
local ports=cpu.spaces["io"]
local vram=machine.devices[":tms9918a"].spaces["vram"]
local screen=machine.screens[":screen"]
local key=machine.ioport.ports[os.getenv("CT_MODE")=="two" and ":sgexp:sk1100:PB5" or ":sgexp:sk1100:PA3"]:field(os.getenv("CT_MODE")=="two" and 8 or 16)
local directory=assert(os.getenv("CT_MODE_OUTPUT"))
local regs,latch,taps={},nil,{}
local masks={3,251,15,255,7,127,7,255}
taps[1]=ports:install_write_tap(0xbf,0xbf,"mode-regs",function(_,value)
 if latch==nil then latch=value else
  if value&128~=0 then regs[value&7]=latch&masks[(value&7)+1] end
  latch=nil
 end
end)
for i,address in ipairs({0xbe,0xbf}) do
 taps[#taps+1]=ports:install_read_tap(address,address,"mode-latch",function() latch=nil end)
end
taps[#taps+1]=ports:install_write_tap(0xbe,0xbe,"mode-data",function() latch=nil end)
local function dump(path,space,first,last)
 local file=assert(io.open(path,"wb"))
 for address=first,last do file:write(string.char(space:read_u8(address))) end
 file:close()
end
local frame=0
emu.register_frame_done(function()
 assert(#taps==4)
 frame=frame+1
 if frame==120 then key:set_value(1) end
 if frame==420 then key:clear_value() end
 if frame==119 or frame==300 or frame==1299 then
  local stem=directory..string.format("/f%05d",frame)
  dump(stem..".ram",ram,0xc000,0xc3ff)
  dump(stem..".vram",vram,0,0x3fff)
  local file=assert(io.open(stem..".regs","wb"))
  for i=0,7 do file:write(string.char(assert(regs[i]))) end
  file:close()
  local pixels,width,height=screen:pixels()
  file=assert(io.open(stem..".pixels","wb"));file:write(pixels);file:close()
  file=assert(io.open(stem..".raster","w"));file:write(width.." "..height);file:close()
 end
 if frame==1300 then print("MODE_REFERENCE_COMPLETE");machine:exit() end
end)
