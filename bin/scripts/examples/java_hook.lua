-- Test script for Java String return values
-- Target: com.example.reneftestapp

print("[*] Starting Java String hook test...")

-- Hook childHook - modify return value
hook("com/example/reneftestapp/MainActivity", "childHook", "(Ljava/lang/String;)Ljava/lang/String;", {
    onEnter = function(args)
        print("[+] childHook called")
        print("    this = " .. string.format("0x%x", args[1]))
        print("    param (jstring ref) = " .. string.format("0x%x", args[2]))
    end,
    onLeave = function(retval)
        print("[+] childHook onLeave")
        print("    Original: \"" .. (retval.value or "nil") .. "\"")

        -- Modify the return value!
        local newValue = "HOOKED BY RENEF!"
        print("    Replacing with: \"" .. newValue .. "\"")

        return JNI.string(newValue)
    end
})

-- Hook parentHook - just observe
hook("com/example/reneftestapp/MainActivity", "parentHook", "(Ljava/lang/String;)Ljava/lang/String;", {
    onEnter = function(args)
        print("[+] parentHook called")
        print("    this = " .. string.format("0x%x", args[1]))
        print("    param (jstring ref) = " .. string.format("0x%x", args[2]))
    end,
    onLeave = function(retval)
        print("[+] parentHook onLeave")
        print("    Return (raw ref): " .. string.format("0x%x", retval.raw))
        if retval.value then
            print("    Return (string): \"" .. retval.value .. "\"")
        end
        return retval.raw
    end
})

print("[+] Hooks installed!")
print("[*] childHook return value will be replaced with 'HOOKED BY RENEF!'")
