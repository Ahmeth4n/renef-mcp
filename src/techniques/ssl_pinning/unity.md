## 9. Unity

Unity games/apps can implement SSL pinning through C# scripts or native plugins.

### 9.1 How Unity Networking Works

```
┌─────────────────────────────────────────────────────────────┐
│                    C# Scripts                                │
│   UnityWebRequest / WWW / .NET HttpClient                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    IL2CPP / Mono                             │
│              Compiled C# code                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Native Platform Layer                           │
│   Android: uses Java network stack via JNI                  │
│   IL2CPP: libil2cpp.so                                      │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Unity Pinning Implementations

#### Method 1: CertificateHandler Class

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Security.Cryptography.X509Certificates;

public class PinnedCertificateHandler : CertificateHandler
{
    // SHA-256 hash of the server's public key
    private static readonly string[] PINS = {
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
    };
    
    protected override bool ValidateCertificate(byte[] certificateData)
    {
        try
        {
            var cert = new X509Certificate2(certificateData);
            var publicKey = cert.GetPublicKey();
            
            using (var sha256 = System.Security.Cryptography.SHA256.Create())
            {
                var hash = sha256.ComputeHash(publicKey);
                var hashBase64 = System.Convert.ToBase64String(hash);
                
                foreach (var pin in PINS)
                {
                    if (hashBase64 == pin)
                    {
                        Debug.Log("Certificate pin matched!");
                        return true;
                    }
                }
            }
            
            Debug.LogError("Certificate pinning failed!");
            return false;
        }
        catch (System.Exception e)
        {
            Debug.LogError("Certificate validation error: " + e.Message);
            return false;
        }
    }
}

// Usage
public class ApiClient : MonoBehaviour
{
    IEnumerator FetchData(string url)
    {
        using (var request = UnityWebRequest.Get(url))
        {
            request.certificateHandler = new PinnedCertificateHandler();
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("Data: " + request.downloadHandler.text);
            }
            else
            {
                Debug.LogError("Request failed: " + request.error);
            }
        }
    }
}
```

#### Method 2: Native Plugin Pinning

```csharp
// C# wrapper
public class NativeSSLPinning
{
    #if UNITY_ANDROID && !UNITY_EDITOR
    private static AndroidJavaObject pinnedClient;
    
    public static void Initialize(string[] pins)
    {
        using (var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        {
            var activity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
            var context = activity.Call<AndroidJavaObject>("getApplicationContext");
            
            pinnedClient = new AndroidJavaObject(
                "com.game.ssl.PinnedHttpClient",
                context,
                new AndroidJavaObject("java.util.ArrayList", pins)
            );
        }
    }
    
    public static string Request(string url)
    {
        return pinnedClient.Call<string>("request", url);
    }
    #endif
}
```

### 9.3 Unity Bypass Techniques

#### Method 1: Hook CertificateHandler (Frida / Renef + IL2CPP)

```javascript
// For IL2CPP builds
function bypassUnityCertHandler() {
    // Find il2cpp
    var il2cpp = Process.findModuleByName('libil2cpp.so');
    if (!il2cpp) {
        console.log('[-] libil2cpp.so not found');
        return;
    }
    
    console.log('[+] libil2cpp.so at: ' + il2cpp.base);
    
    // Search for CertificateHandler::ValidateCertificate
    // This requires finding the method through IL2CPP metadata
    
    // Alternative: Hook at the Java layer
    Java.perform(function() {
        // Unity ultimately uses Android's SSL stack
        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        
        var BypassTrustManager = Java.registerClass({
            name: 'com.unity.bypass.TrustManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        
        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        SSLContext.init.overload(
            '[Ljavax.net.ssl.KeyManager;',
            '[Ljavax.net.ssl.TrustManager;',
            'java.security.SecureRandom'
        ).implementation = function(km, tm, sr) {
            console.log('[+] Unity SSLContext.init bypassed');
            this.init(km, [BypassTrustManager.$new()], sr);
        };
    });
}

bypassUnityCertHandler();
```

#### Method 2: Patch IL2CPP Binary

```python
#!/usr/bin/env python3
"""
Unity IL2CPP Certificate Handler Patcher
Patches ValidateCertificate to always return true
"""

import sys
import struct

def patch_il2cpp(filename, output):
    with open(filename, 'rb') as f:
        data = bytearray(f.read())
    
    # Search for ValidateCertificate return pattern
    # ARM64: MOV W0, #0 (failure) followed by RET
    # We change to MOV W0, #1 (success)
    
    # Pattern varies by Unity version
    patterns = [
        (b'\x00\x00\x80\x52\xc0\x03\x5f\xd6', 
         b'\x20\x00\x80\x52\xc0\x03\x5f\xd6'),  # MOV W0,#0;RET -> MOV W0,#1;RET
    ]
    
    patched = 0
    for original, replacement in patterns:
        idx = 0
        while True:
            idx = data.find(original, idx)
            if idx == -1:
                break
            data[idx:idx+len(replacement)] = replacement
            patched += 1
            idx += len(replacement)
            print(f'[+] Patched at offset 0x{idx:x}')
    
    if patched > 0:
        with open(output, 'wb') as f:
            f.write(data)
        print(f'[+] Saved patched binary with {patched} patches')
    else:
        print('[-] No patterns found')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <libil2cpp.so> <output.so>')
        sys.exit(1)
    patch_il2cpp(sys.argv[1], sys.argv[2])
```

#### Method 3: Hook via Unity's Mono (for Mono builds)

```javascript
// For Mono builds (not IL2CPP)
Java.perform(function() {
    // Find the CertificateHandler class in Mono
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('CertificateHandler')) {
                console.log('[+] Found: ' + className);
                try {
                    var clazz = Java.use(className);
                    // Hook ValidateCertificate
                    if (clazz.ValidateCertificate) {
                        clazz.ValidateCertificate.implementation = function(data) {
                            console.log('[*] Unity CertificateHandler bypassed');
                            return true;
                        };
                    }
                } catch(e) {}
            }
        },
        onComplete: function() {}
    });
});
```

---

