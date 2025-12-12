## 13. Detection and Anti-Tampering

### 13.1 How Apps Detect Bypass Attempts

#### Root Detection
```java
public class RootDetector {
    
    private static final String[] ROOT_PATHS = {
        "/system/app/Superuser.apk",
        "/sbin/su",
        "/system/bin/su",
        "/system/xbin/su",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/system/sd/xbin/su",
        "/system/bin/failsafe/su",
        "/data/local/su",
        "/su/bin/su"
    };
    
    private static final String[] DANGEROUS_PACKAGES = {
        "com.topjohnwu.magisk",
        "eu.chainfire.supersu",
        "com.koushikdutta.superuser",
        "com.noshufou.android.su",
        "com.thirdparty.superuser"
    };
    
    public static boolean isDeviceRooted() {
        return checkRootBinaries() || 
               checkRootPackages() || 
               checkBuildTags() ||
               checkSuCommand();
    }
}
```

#### Frida / Renef Detection
```java
public class Frida / RenefDetector {
    
    public static boolean isFrida / RenefPresent() {
        // Check for Frida / Renef server port
        if (isPortOpen(27042)) return true;
        if (isPortOpen(27043)) return true;
        
        // Check for Frida / Renef libraries in memory
        try {
            BufferedReader reader = new BufferedReader(
                new FileReader("/proc/self/maps")
            );
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.contains("Frida / Renef") || line.contains("gadget")) {
                    return true;
                }
            }
        } catch (IOException e) {}
        
        // Check for Frida / Renef named threads
        for (Thread thread : Thread.getAllStackTraces().keySet()) {
            if (thread.getName().contains("Frida / Renef") ||
                thread.getName().contains("gum-js-loop")) {
                return true;
            }
        }
        
        return false;
    }
}
```

#### Certificate Transparency
```java
// Server-side enforcement of Certificate Transparency
// Client can also validate CT signatures

public class CTValidator {
    
    public boolean validateCertificateTransparency(
        X509Certificate cert, 
        List<SignedCertificateTimestamp> scts
    ) {
        // Verify SCT signatures from known CT logs
        for (SignedCertificateTimestamp sct : scts) {
            if (!verifySCTSignature(cert, sct)) {
                return false;
            }
        }
        
        // Require at least 2 SCTs from different logs
        return scts.size() >= 2;
    }
}
```

### 13.2 Bypassing Anti-Tampering

```javascript
// Comprehensive anti-detection bypass
Java.perform(function() {
    
    // 1. Hide Root
    var Runtime = Java.use('java.lang.Runtime');
    Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
        if (cmd.includes('su') || cmd.includes('which')) {
            console.log('[*] Blocked root check command: ' + cmd);
            throw new Error('Command not found');
        }
        return this.exec(cmd);
    };
    
    // 2. Hide Frida / Renef
    var Thread = Java.use('java.lang.Thread');
    Thread.getName.implementation = function() {
        var name = this.getName();
        if (name.includes('Frida / Renef') || name.includes('gum')) {
            return 'main'; // Return innocuous name
        }
        return name;
    };
    
    // 3. Fake Build Properties
    var Build = Java.use('android.os.Build');
    Build.TAGS.value = 'release-keys';
    Build.FINGERPRINT.value = Build.FINGERPRINT.value.replace('test-keys', 'release-keys');
    
    // 4. Hide Xposed
    try {
        var XposedBridge = Java.use('de.robv.android.xposed.XposedBridge');
        XposedBridge.disableHooks.value = true;
    } catch(e) {}
    
    // 5. Bypass SafetyNet (basic)
    try {
        var SafetyNet = Java.use('com.google.android.gms.safetynet.SafetyNetClient');
        SafetyNet.attest.implementation = function(nonce, apiKey) {
            console.log('[*] SafetyNet attestation intercepted');
            // Return fake successful attestation
        };
    } catch(e) {}
    
    // 6. Anti-Debug Bypass
    var Debug = Java.use('android.os.Debug');
    Debug.isDebuggerConnected.implementation = function() {
        console.log('[*] Debug.isDebuggerConnected() - returning false');
        return false;
    };
    
    Debug.waitingForDebugger.implementation = function() {
        return false;
    };
});
```

---

