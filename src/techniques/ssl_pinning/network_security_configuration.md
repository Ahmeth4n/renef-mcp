## 10. Network Security Configuration (Deep Dive)

### 10.1 Complete Configuration Reference

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    
    <!-- 
    Base configuration: Applied to all connections unless overridden
    -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <!-- System trusted CAs -->
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    
    <!--
    Domain-specific configurations
    More specific configs override less specific ones
    -->
    
    <!-- Main API domain with pinning -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        
        <!-- Certificate pins -->
        <pin-set expiration="2025-12-31">
            <!-- Leaf certificate pin -->
            <pin digest="SHA-256">7HIpactkIAq2Y49orFOOQKurWxmmSFZhBCoQYcRhJ3Y=</pin>
            <!-- Intermediate CA pin (backup) -->
            <pin digest="SHA-256">fwza0LRMXouZHRC8Ei+4PyuldPDcf3UKgO/04cDM1oE=</pin>
        </pin-set>
        
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </domain-config>
    
    <!-- CDN domain - different pins -->
    <domain-config>
        <domain includeSubdomains="true">cdn.example.com</domain>
        <pin-set>
            <pin digest="SHA-256">CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=</pin>
        </pin-set>
    </domain-config>
    
    <!-- Internal domain - allow self-signed in specific conditions -->
    <domain-config>
        <domain>internal.example.com</domain>
        <trust-anchors>
            <!-- Trust a specific CA certificate bundled with app -->
            <certificates src="@raw/internal_ca" />
        </trust-anchors>
    </domain-config>
    
    <!--
    Debug overrides - ONLY active when android:debuggable="true"
    -->
    <debug-overrides>
        <trust-anchors>
            <!-- Trust user-installed certificates (e.g., Burp, Charles) -->
            <certificates src="user" />
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
    
</network-security-config>
```

### 10.2 How Android Processes Network Security Config

```java
// Simplified view of Android's internal processing

public class NetworkSecurityConfig {
    
    public static NetworkSecurityConfig getConfigForHostname(String hostname) {
        // 1. Check domain-specific configs (most specific first)
        for (DomainConfig config : domainConfigs) {
            if (config.matches(hostname)) {
                return config;
            }
        }
        
        // 2. Fall back to base config
        return baseConfig;
    }
    
    public boolean checkPins(List<X509Certificate> chain) {
        if (pins.isEmpty()) {
            return true; // No pins configured
        }
        
        if (pins.isExpired()) {
            return true; // Pins expired, don't enforce
        }
        
        for (X509Certificate cert : chain) {
            byte[] spki = cert.getPublicKey().getEncoded();
            byte[] hash = sha256(spki);
            
            for (Pin pin : pins) {
                if (Arrays.equals(hash, pin.getHash())) {
                    return true; // Pin matched
                }
            }
        }
        
        return false; // No pin matched
    }
}
```

### 10.3 Advanced NSC Bypass

```javascript
// Comprehensive Network Security Config Bypass
Java.perform(function() {
    console.log('[*] Network Security Config Bypass Starting...');
    
    // Method 1: Hook NetworkSecurityConfig directly
    try {
        var NetworkSecurityConfig = Java.use(
            'android.security.net.config.NetworkSecurityConfig'
        );
        
        // Bypass pin checking
        NetworkSecurityConfig.checkPins.implementation = function(chain) {
            console.log('[+] NetworkSecurityConfig.checkPins bypassed');
            return true;
        };
    } catch(e) {
        console.log('[-] NetworkSecurityConfig not found: ' + e);
    }
    
    // Method 2: Hook NetworkSecurityTrustManager
    try {
        var NetworkSecurityTrustManager = Java.use(
            'android.security.net.config.NetworkSecurityTrustManager'
        );
        
        NetworkSecurityTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String'
        ).implementation = function(chain, authType) {
            console.log('[+] NetworkSecurityTrustManager bypassed');
        };
        
        // Also hook the hostname-aware version
        NetworkSecurityTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String',
            'java.lang.String'
        ).implementation = function(chain, authType, host) {
            console.log('[+] NetworkSecurityTrustManager bypassed for: ' + host);
        };
    } catch(e) {
        console.log('[-] NetworkSecurityTrustManager hook failed: ' + e);
    }
    
    // Method 3: Hook PinSet validation
    try {
        var PinSet = Java.use('android.security.net.config.PinSet');
        
        PinSet.getPins.implementation = function() {
            console.log('[+] PinSet.getPins returning empty set');
            return Java.use('java.util.Collections').emptySet();
        };
    } catch(e) {}
    
    // Method 4: Hook ManifestConfigSource to prevent config loading
    try {
        var ManifestConfigSource = Java.use(
            'android.security.net.config.ManifestConfigSource'
        );
        
        ManifestConfigSource.getConfigResource.implementation = function() {
            console.log('[+] Preventing NSC resource loading');
            return 0; // Return invalid resource ID
        };
    } catch(e) {}
    
    console.log('[+] Network Security Config Bypass Complete');
});
```

---

