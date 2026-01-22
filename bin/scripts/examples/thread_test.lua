-- Thread backtrace test script

local tid = Thread.id()
print(string.format("pid: %d, tid: %d", tid, tid))
print("backtrace:")

local bt = Thread.backtrace()

for i, frame in ipairs(bt) do
    local pc_str = string.format("%016x", frame.pc)
    local offset_str = ""
    local symbol_str = ""
    local path_str = frame.path or frame.module or "<unknown>"

    if frame.offset then
        offset_str = string.format("+%d", frame.offset)
    end

    if frame.symbol then
        symbol_str = string.format(" (%s%s)", frame.symbol, offset_str)
    elseif frame.offset then
        symbol_str = string.format(" (offset 0x%x)", frame.offset)
    end

    print(string.format("    #%02d pc %s  %s%s",
        frame.index,
        pc_str,
        path_str,
        symbol_str))
end
