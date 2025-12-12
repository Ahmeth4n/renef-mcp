## 4. Native Android (Java/Kotlin)

### 4.1 TrustManager Implementation

The most fundamental way to implement SSL pinning in Android is by creating a custom `X509TrustManager`.

#### Implementation (Java)

```java
public class PinningTrustManager implements X509TrustManager {
    
    // SHA-256 hash of the server's public key
    private static final String[] PINS = {
        "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="  // Backup pin
    };
    
    private final X509TrustManager defaultTrustManager;
    
    public PinningTrustManager() throws Exception {
        TrustManagerFactory tmf = TrustManagerFactory.getInstance(
            TrustManagerFactory.getDefaultAlgorithm());
        tmf.init((KeyStore) null);
        
        for (TrustManager tm : tmf.getTrustManagers()) {
            if (tm instanceof X509TrustManager) {
                defaultTrustManager = (X509TrustManager) tm;
                return;
            }
        }
        throw new IllegalStateException("No X509TrustManager found");
    }
    
    @Override
    public void checkServerTrusted(X509Certificate[] chain, String authType)
            throws CertificateException {
        // First, do standard validation
        defaultTrustManager.checkServerTrusted(chain, authType);
        
        // Then verify pin
        if (!isPinValid(chain)) {
            throw new CertificateException("Certificate pinning failure!");
        }
    }
    
    private boolean isPinValid(X509Certificate[] chain) {
        for (X509Certificate cert : chain) {
            String certPin = getPublicKeyPin(cert);
            for (String pin : PINS) {
                if (pin.equals("sha256/" + certPin)) {
                    return true;
                }
            }
        }
        return false;
    }
    
    private String getPublicKeyPin(X509Certificate cert) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] publicKeyBytes = cert.getPublicKey().getEncoded();
            byte[] hash = md.digest(publicKeyBytes);
            return Base64.encodeToString(hash, Base64.NO_WRAP);
        } catch (Exception e) {
            return "";
        }
    }
    
    @Override
    public void checkClientTrusted(X509Certificate[] chain, String authType) 
            throws CertificateException {
        defaultTrustManager.checkClientTrusted(chain, authType);
    }
    
    @Override
    public X509Certificate[] getAcceptedIssuers() {
        return defaultTrustManager.getAcceptedIssuers();
    }
}
```

#### Usage with HttpsURLConnection

```java
public class SecureConnection {
    
    public static HttpsURLConnection createPinnedConnection(String urlString) 
            throws Exception {
        URL url = new URL(urlString);
        HttpsURLConnection connection = (HttpsURLConnection) url.openConnection();
        
        // Create SSLContext with pinning TrustManager
        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(null, new TrustManager[]{new PinningTrustManager()}, null);
        
        connection.setSSLSocketFactory(sslContext.getSocketFactory());
        
        // Optional: Also verify hostname
        connection.setHostnameVerifier((hostname, session) -> {
            return hostname.equals("api.example.com");
        });
        
        return connection;
    }
}
```

#### Bypass Techniques for TrustManager

**Method 1: Hook checkServerTrusted (Frida / Renef)**
```javascript
// Frida / Renef script to bypass TrustManager
Java.perform(function() {
    // Hook X509TrustManager implementations
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    
    // Create a TrustManager that trusts everything
    var TrustManager = Java.registerClass({
        name: 'com.bypass.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    // Hook SSLContext.init to inject our TrustManager
    SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;',
        '[Ljavax.net.ssl.TrustManager;',
        'java.security.SecureRandom'
    ).implementation = function(km, tm, sr) {
        console.log('[*] SSLContext.init intercepted');
        this.init(km, [TrustManager.$new()], sr);
    };
});
```

**Method 2: Hook specific app's TrustManager (Frida / Renef)**
```javascript
Java.perform(function() {
    // Find all classes implementing X509TrustManager
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('TrustManager') || 
                className.includes('Pinning') ||
                className.includes('Certificate')) {
                try {
                    var clazz = Java.use(className);
                    if (clazz.checkServerTrusted) {
                        console.log('[+] Found: ' + className);
                        clazz.checkServerTrusted.overload(
                            '[Ljava.security.cert.X509Certificate;', 
                            'java.lang.String'
                        ).implementation = function(chain, authType) {
                            console.log('[*] Bypassing: ' + className);
                            return;
                        };
                    }
                } catch(e) {}
            }
        },
        onComplete: function() {}
    });
});
```

**Method 3: Patch APK (Smali modification)**
```smali
# Original checkServerTrusted method
.method public checkServerTrusted([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V
    .locals 2
    
    # Original pinning logic here...
    
    # Throws CertificateException if pin doesn't match
    new-instance v0, Ljava/security/cert/CertificateException;
    const-string v1, "Pin mismatch"
    invoke-direct {v0, v1}, Ljava/security/cert/CertificateException;-><init>(Ljava/lang/String;)V
    throw v0
.end method

# Patched version - just return without checking
.method public checkServerTrusted([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V
    .locals 0
    return-void
.end method
```

---

### 4.2 OkHttp CertificatePinner

OkHttp is the most popular HTTP client for Android and provides built-in certificate pinning.

#### Implementation (Kotlin)

```kotlin
class NetworkClient {
    
    private val certificatePinner = CertificatePinner.Builder()
        // Pin the leaf certificate
        .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        // Pin intermediate CA (backup)
        .add("api.example.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")
        // Wildcard domain pinning
        .add("*.example.com", "sha256/CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=")
        .build()
    
    val okHttpClient = OkHttpClient.Builder()
        .certificatePinner(certificatePinner)
        .connectTimeout(30, TimeUnit.SECONDS)
        .build()
    
    // For Retrofit
    val retrofit = Retrofit.Builder()
        .baseUrl("https://api.example.com/")
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
```

#### How OkHttp Pinning Works Internally

```
Request → OkHttp → RealCall → ConnectInterceptor
                                      ↓
                              RealConnection.connect()
                                      ↓
                              SSL Handshake
                                      ↓
                              CertificatePinner.check()
                                      ↓
                              Compare pins against chain
                                      ↓
                         Match? → Continue : throw SSLPeerUnverifiedException
```

#### OkHttp CertificatePinner Source Code Analysis

```java
// Simplified version of OkHttp's pinning logic
public void check(String hostname, List<Certificate> peerCertificates) 
        throws SSLPeerUnverifiedException {
    
    List<Pin> pins = findMatchingPins(hostname);
    if (pins.isEmpty()) return; // No pins configured for this host
    
    for (Certificate certificate : peerCertificates) {
        X509Certificate x509 = (X509Certificate) certificate;
        
        // Calculate pin for this certificate
        ByteString publicKeyPin = sha256(x509.getPublicKey().getEncoded());
        
        for (Pin pin : pins) {
            if (pin.hash.equals(publicKeyPin)) {
                return; // Pin matched!
            }
        }
    }
    
    // No pin matched - throw exception
    throw new SSLPeerUnverifiedException(
        "Certificate pinning failure!\n" +
        "Peer certificate chain:\n" + 
        certificateChainDescription(peerCertificates) +
        "\nPinned certificates:\n" + 
        pins
    );
}
```

#### Bypass Techniques for OkHttp

**Method 1: Hook CertificatePinner.check (Frida / Renef)**
```javascript
Java.perform(function() {
    var CertificatePinner = Java.use('okhttp3.CertificatePinner');
    
    // Hook check method
    CertificatePinner.check.overload(
        'java.lang.String', 
        'java.util.List'
    ).implementation = function(hostname, peerCertificates) {
        console.log('[*] OkHttp CertificatePinner.check bypassed for: ' + hostname);
        return;
    };
    
    // Also hook the variant with varargs
    CertificatePinner.check.overload(
        'java.lang.String',
        '[Ljava.security.cert.Certificate;'
    ).implementation = function(hostname, certificates) {
        console.log('[*] OkHttp CertificatePinner.check (varargs) bypassed');
        return;
    };
});
```

**Method 2: Hook CertificatePinner.Builder (Frida / Renef)**
```javascript
Java.perform(function() {
    var CertificatePinner$Builder = Java.use('okhttp3.CertificatePinner$Builder');
    
    // Make add() do nothing
    CertificatePinner$Builder.add.overload(
        'java.lang.String',
        '[Ljava.lang.String;'
    ).implementation = function(hostname, pins) {
        console.log('[*] Prevented pin addition for: ' + hostname);
        return this; // Return builder without adding pins
    };
});
```

**Method 3: Replace CertificatePinner with empty one**
```javascript
Java.perform(function() {
    var OkHttpClient$Builder = Java.use('okhttp3.OkHttpClient$Builder');
    var CertificatePinner = Java.use('okhttp3.CertificatePinner');
    
    OkHttpClient$Builder.certificatePinner.implementation = function(pinner) {
        console.log('[*] Replacing CertificatePinner with empty one');
        var emptyPinner = CertificatePinner.DEFAULT;
        return this.certificatePinner(emptyPinner);
    };
});
```

---

### 4.3 Network Security Configuration (Android 7.0+)

Android's declarative XML-based pinning mechanism.

#### Implementation (res/xml/network_security_config.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    
    <!-- Base configuration for all domains -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    
    <!-- Domain-specific configuration with pinning -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        
        <!-- Pin configuration -->
        <pin-set expiration="2025-12-31">
            <!-- Primary pin (leaf certificate) -->
            <pin digest="SHA-256">AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</pin>
            <!-- Backup pin (intermediate CA) -->
            <pin digest="SHA-256">BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=</pin>
        </pin-set>
        
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </domain-config>
    
    <!-- Debug overrides (only active in debug builds) -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />  <!-- Allow user-installed CAs -->
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
    
</network-security-config>
```

#### AndroidManifest.xml Configuration

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
</application>
```

#### How Network Security Config Works Internally

```
┌─────────────────────────────────────────────────────────────┐
│                    NetworkSecurityConfig                      │
│  (Parsed at app startup from XML)                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              ApplicationConfig                                │
│  - Base config                                               │
│  - Domain configs (sorted by specificity)                    │
│  - Debug overrides                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│    NetworkSecurityTrustManager                               │
│    (Wraps default TrustManager)                              │
│                                                              │
│    checkServerTrusted() {                                    │
│        1. Standard chain validation                          │
│        2. Check pins if configured for domain                │
│        3. Verify expiration of pin-set                       │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
```

#### Bypass Techniques for Network Security Config

**Method 1: Modify APK's network_security_config.xml**
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />  <!-- Trust user CAs -->
        </trust-anchors>
    </base-config>
</network-security-config>
```

**Method 2: Hook NetworkSecurityTrustManager (Frida / Renef)**
```javascript
Java.perform(function() {
    // Android 7.0+ NetworkSecurityConfig bypass
    try {
        var NetworkSecurityTrustManager = Java.use(
            'android.security.net.config.NetworkSecurityTrustManager'
        );
        
        NetworkSecurityTrustManager.checkPins.implementation = function(chain) {
            console.log('[*] NetworkSecurityConfig pin check bypassed');
            return;
        };
    } catch(e) {
        console.log('[-] NetworkSecurityTrustManager not found');
    }
    
    // Also try RootTrustManager
    try {
        var RootTrustManager = Java.use(
            'android.security.net.config.RootTrustManager'
        );
        
        RootTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String'
        ).implementation = function(chain, authType) {
            console.log('[*] RootTrustManager.checkServerTrusted bypassed');
        };
    } catch(e) {}
});
```

**Method 3: Patch AndroidManifest.xml**
Remove or modify the `networkSecurityConfig` attribute:
```bash
# Decompile APK
apktool d app.apk -o app_decoded

# Edit AndroidManifest.xml - remove networkSecurityConfig
# Or replace with permissive config

# Rebuild and sign
apktool b app_decoded -o app_patched.apk
jarsigner -keystore debug.keystore app_patched.apk androiddebugkey
```

---

### 4.4 WebView SSL Pinning

For apps using WebView to load secure content.

#### Implementation

```kotlin
class PinningWebViewClient : WebViewClient() {
    
    private val pins = setOf(
        "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
    )
    
    override fun onReceivedSslError(
        view: WebView?,
        handler: SslErrorHandler?,
        error: SslError?
    ) {
        // Never call handler.proceed() on SSL errors in production!
        handler?.cancel()
        Log.e("SSL", "SSL Error: ${error?.primaryError}")
    }
    
    // For API 21+
    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    override fun onReceivedClientCertRequest(
        view: WebView?,
        request: ClientCertRequest?
    ) {
        // Handle client certificate if needed
        request?.cancel()
    }
}

// Additional pinning for WebView (requires custom SSL handling)
class SecureWebView(context: Context) : WebView(context) {
    
    init {
        settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        }
        
        webViewClient = PinningWebViewClient()
    }
}
```

#### WebView Pinning via Interceptor (OkHttp + WebViewAssetLoader)

```kotlin
class WebViewWithPinning(context: Context) {
    
    private val okHttpClient = OkHttpClient.Builder()
        .certificatePinner(
            CertificatePinner.Builder()
                .add("example.com", "sha256/...")
                .build()
        )
        .build()
    
    private val assetLoader = WebViewAssetLoader.Builder()
        .addPathHandler("/proxy/", object : WebViewAssetLoader.PathHandler {
            override fun handle(path: String): WebResourceResponse? {
                // Use OkHttp with pinning to fetch resources
                val request = Request.Builder()
                    .url("https://example.com/$path")
                    .build()
                
                return try {
                    val response = okHttpClient.newCall(request).execute()
                    WebResourceResponse(
                        response.header("Content-Type") ?: "text/html",
                        "UTF-8",
                        response.body?.byteStream()
                    )
                } catch (e: Exception) {
                    null
                }
            }
        })
        .build()
}
```

#### Bypass Techniques for WebView

```javascript
Java.perform(function() {
    var WebViewClient = Java.use('android.webkit.WebViewClient');
    
    // Bypass onReceivedSslError
    WebViewClient.onReceivedSslError.overload(
        'android.webkit.WebView',
        'android.webkit.SslErrorHandler',
        'android.net.http.SslError'
    ).implementation = function(view, handler, error) {
        console.log('[*] WebView SSL error bypassed');
        handler.proceed(); // Accept all certificates
    };
    
    // Also hook custom WebViewClient implementations
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('WebViewClient')) {
                try {
                    var clazz = Java.use(className);
                    if (clazz.onReceivedSslError) {
                        clazz.onReceivedSslError.overload(
                            'android.webkit.WebView',
                            'android.webkit.SslErrorHandler', 
                            'android.net.http.SslError'
                        ).implementation = function(view, handler, error) {
                            console.log('[*] Custom WebViewClient bypassed: ' + className);
                            handler.proceed();
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

