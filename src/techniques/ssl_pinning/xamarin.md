## 7. Xamarin

Xamarin apps can implement SSL pinning through both C# managed code and native platform code.

### 7.1 How Xamarin Networking Works

```
┌─────────────────────────────────────────────────────────────┐
│                    C# / .NET Code                            │
│   HttpClient / WebClient / RestSharp                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mono Runtime                              │
│              HttpClientHandler / WebRequestHandler           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Platform-Specific Handler                       │
│   AndroidClientHandler (uses OkHttp/HttpURLConnection)      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Xamarin Pinning Implementations

#### Method 1: ServicePointManager.ServerCertificateValidationCallback

```csharp
using System.Net;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;

public class PinnedHttpClient
{
    private static readonly string[] PinnedPublicKeys = {
        "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
    };
    
    static PinnedHttpClient()
    {
        ServicePointManager.ServerCertificateValidationCallback = 
            ValidateServerCertificate;
    }
    
    private static bool ValidateServerCertificate(
        object sender,
        X509Certificate certificate,
        X509Chain chain,
        SslPolicyErrors sslPolicyErrors)
    {
        // First check for standard SSL errors
        if (sslPolicyErrors != SslPolicyErrors.None)
            return false;
        
        // Then verify pin
        foreach (var chainElement in chain.ChainElements)
        {
            var publicKey = chainElement.Certificate.GetPublicKey();
            var hash = ComputeSha256Hash(publicKey);
            var pin = $"sha256/{Convert.ToBase64String(hash)}";
            
            if (PinnedPublicKeys.Contains(pin))
                return true;
        }
        
        return false;
    }
    
    private static byte[] ComputeSha256Hash(byte[] data)
    {
        using (var sha256 = SHA256.Create())
        {
            return sha256.ComputeHash(data);
        }
    }
}
```

#### Method 2: Custom HttpClientHandler

```csharp
public class PinningHandler : HttpClientHandler
{
    private readonly string[] _pins;
    
    public PinningHandler(params string[] pins)
    {
        _pins = pins;
        ServerCertificateCustomValidationCallback = ValidateCertificate;
    }
    
    private bool ValidateCertificate(
        HttpRequestMessage request,
        X509Certificate2 certificate,
        X509Chain chain,
        SslPolicyErrors errors)
    {
        if (errors != SslPolicyErrors.None)
            return false;
        
        // Check each certificate in chain
        foreach (var element in chain.ChainElements)
        {
            var cert = element.Certificate;
            using (var sha256 = SHA256.Create())
            {
                var hash = sha256.ComputeHash(cert.GetPublicKey());
                var pin = "sha256/" + Convert.ToBase64String(hash);
                
                if (_pins.Contains(pin))
                    return true;
            }
        }
        
        return false;
    }
}

// Usage
var handler = new PinningHandler(
    "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
);
var client = new HttpClient(handler);
```

#### Method 3: ModernHttpClient with Pinning

```csharp
// Using ModernHttpClient with native handlers
public class NativePinningHandler
{
    public static HttpClient CreatePinnedClient()
    {
        // Uses OkHttp on Android
        var handler = new NativeMessageHandler(
            throwOnCaptiveNetwork: true,
            customSSLVerification: true
        );
        
        // Add certificate validation
        handler.ServerCertificateCustomValidationCallback = 
            (message, cert, chain, errors) =>
            {
                return ValidatePin(cert, chain);
            };
        
        return new HttpClient(handler);
    }
}
```

### 7.3 Xamarin Bypass Techniques

#### Method 1: Hook Mono Runtime (Frida / Renef)

```javascript
Java.perform(function() {
    // Hook Mono's certificate validation
    
    // Find Mono internal methods
    var monoClasses = [];
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('mono') || 
                className.includes('Mono') ||
                className.includes('Xamarin')) {
                monoClasses.push(className);
            }
        },
        onComplete: function() {}
    });
    
    console.log('[*] Found Mono classes: ' + monoClasses.length);
    
    // Hook certificate validation callback
    try {
        // This hooks the underlying Android implementation
        var X509TrustManagerExtensions = Java.use(
            'android.net.http.X509TrustManagerExtensions'
        );
        
        X509TrustManagerExtensions.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String',
            'java.lang.String'
        ).implementation = function(chain, authType, host) {
            console.log('[+] Xamarin/Mono SSL check bypassed for: ' + host);
            return chain;
        };
    } catch(e) {
        console.log('[-] X509TrustManagerExtensions hook failed');
    }
});
```

#### Method 2: Patch Managed DLL

```csharp
// Using dnSpy or ILSpy to patch the validation method
// Find and modify the ValidateCertificate method to always return true

// Before:
private bool ValidateCertificate(...) {
    // Validation logic
    return isValid;
}

// After (patched):
private bool ValidateCertificate(...) {
    return true; // Always accept
}
```

#### Method 3: Hook Native Android Layer

```javascript
// Xamarin ultimately uses Android's SSL implementation
Java.perform(function() {
    // Standard TrustManager bypass works for Xamarin
    var TrustManagerFactory = Java.use('javax.net.ssl.TrustManagerFactory');
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    
    var BypassTrustManager = Java.registerClass({
        name: 'com.xamarin.bypass.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    // Replace all TrustManagers
    TrustManagerFactory.getTrustManagers.implementation = function() {
        console.log('[+] Xamarin TrustManagerFactory.getTrustManagers bypassed');
        return [BypassTrustManager.$new()];
    };
});
```

---

