## 12. Advanced Bypass Techniques

### 12.1 Universal SSL Bypass Script

```javascript
/*
 * Universal Android SSL Pinning Bypass
 * Comprehensive script that handles most pinning implementations
 */

Java.perform(function() {
    console.log('');
    console.log('===============================================');
    console.log('   Universal Android SSL Pinning Bypass v2.0');
    console.log('===============================================');
    console.log('');
    
    // ==========================================
    // 1. TrustManager Bypass
    // ==========================================
    
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    
    var TrustManager = Java.registerClass({
        name: 'com.bypass.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    // Hook SSLContext.init()
    SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;',
        '[Ljavax.net.ssl.TrustManager;',
        'java.security.SecureRandom'
    ).implementation = function(km, tm, sr) {
        console.log('[+] SSLContext.init() - Installing bypass TrustManager');
        this.init(km, [TrustManager.$new()], sr);
    };
    
    // ==========================================
    // 2. OkHttp Bypass (v3.x and v4.x)
    // ==========================================
    
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        
        // OkHttp 3.x
        CertificatePinner.check.overload(
            'java.lang.String',
            'java.util.List'
        ).implementation = function(hostname, peerCertificates) {
            console.log('[+] OkHttp3 CertificatePinner.check() bypassed for: ' + hostname);
        };
        
        // OkHttp 4.x (Kotlin)
        try {
            CertificatePinner.check$okhttp.implementation = function(hostname, fn) {
                console.log('[+] OkHttp4 CertificatePinner.check$okhttp() bypassed');
            };
        } catch(e) {}
        
    } catch(e) {
        console.log('[-] OkHttp not found or hook failed');
    }
    
    // ==========================================
    // 3. Network Security Config Bypass (Android 7+)
    // ==========================================
    
    try {
        var NetworkSecurityTrustManager = Java.use(
            'android.security.net.config.NetworkSecurityTrustManager'
        );
        
        NetworkSecurityTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String',
            'java.lang.String'
        ).implementation = function(chain, authType, host) {
            console.log('[+] NetworkSecurityConfig bypassed for: ' + host);
        };
    } catch(e) {}
    
    try {
        var RootTrustManager = Java.use(
            'android.security.net.config.RootTrustManager'
        );
        
        RootTrustManager.checkServerTrusted.implementation = function(chain, authType) {
            console.log('[+] RootTrustManager.checkServerTrusted() bypassed');
        };
    } catch(e) {}
    
    // ==========================================
    // 4. TrustKit Bypass
    // ==========================================
    
    try {
        var PinningTrustManager = Java.use(
            'com.datatheorem.android.trustkit.pinning.PinningTrustManager'
        );
        
        PinningTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String'
        ).implementation = function(chain, authType) {
            console.log('[+] TrustKit PinningTrustManager bypassed');
        };
    } catch(e) {}
    
    // ==========================================
    // 5. WebView Bypass
    // ==========================================
    
    var WebViewClient = Java.use('android.webkit.WebViewClient');
    
    WebViewClient.onReceivedSslError.overload(
        'android.webkit.WebView',
        'android.webkit.SslErrorHandler',
        'android.net.http.SslError'
    ).implementation = function(view, handler, error) {
        console.log('[+] WebView SSL error bypassed');
        handler.proceed();
    };
    
    // ==========================================
    // 6. HttpsURLConnection Bypass
    // ==========================================
    
    try {
        var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');
        
        HttpsURLConnection.setSSLSocketFactory.implementation = function(factory) {
            console.log('[+] HttpsURLConnection.setSSLSocketFactory() intercepted');
            // Use default factory instead of custom pinning factory
        };
        
        HttpsURLConnection.setHostnameVerifier.implementation = function(verifier) {
            console.log('[+] HttpsURLConnection.setHostnameVerifier() intercepted');
            // Don't set custom verifier
        };
    } catch(e) {}
    
    // ==========================================
    // 7. Apache HTTP Client Bypass (Legacy)
    // ==========================================
    
    try {
        var AbstractVerifier = Java.use(
            'org.apache.http.conn.ssl.AbstractVerifier'
        );
        
        AbstractVerifier.verify.overload(
            'java.lang.String',
            '[Ljava.lang.String;',
            '[Ljava.lang.String;',
            'boolean'
        ).implementation = function(host, cns, subjectAlts, strict) {
            console.log('[+] Apache AbstractVerifier.verify() bypassed');
        };
    } catch(e) {}
    
    // ==========================================
    // 8. Conscrypt Bypass (Google's SSL provider)
    // ==========================================
    
    try {
        var ConscryptTrustManager = Java.use(
            'com.google.android.gms.org.conscrypt.TrustManagerImpl'
        );
        
        ConscryptTrustManager.verifyChain.implementation = function(
            untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData
        ) {
            console.log('[+] Conscrypt TrustManagerImpl.verifyChain() bypassed');
            return untrustedChain;
        };
    } catch(e) {}
    
    // ==========================================
    // 9. Dynamic Class Hooking
    // ==========================================
    
    // Hook any class with "Pinning", "TrustManager", or "Certificate" in name
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('PinningTrustManager') ||
                className.includes('CertificatePinner') ||
                className.includes('SSLPinning')) {
                
                try {
                    var clazz = Java.use(className);
                    var methods = clazz.class.getDeclaredMethods();
                    
                    for (var i = 0; i < methods.length; i++) {
                        var method = methods[i];
                        var methodName = method.getName();
                        
                        if (methodName.includes('check') || 
                            methodName.includes('verify') ||
                            methodName.includes('validate')) {
                            
                            console.log('[*] Found method: ' + className + '.' + methodName);
                            // Note: Dynamic hooking would require more complex logic
                        }
                    }
                } catch(e) {}
            }
        },
        onComplete: function() {}
    });
    
    console.log('');
    console.log('[+] SSL Pinning Bypass Active!');
    console.log('');
});
```

### 12.2 Objection Framework Commands

```bash
# Start objection
objection -g com.example.app explore

# Disable SSL pinning
android sslpinning disable

# List all loaded classes
android hooking list classes

# Search for pinning-related classes  
android hooking search classes pin
android hooking search classes cert
android hooking search classes trust

# Hook specific method
android hooking watch class_method com.example.PinningManager.checkPin --dump-args

# Generate Frida / Renef script
android hooking generate simple com.example.PinningManager
```

### 12.3 APK Patching Approach

```bash
#!/bin/bash
# Complete APK SSL pinning removal script

APK_FILE=$1
OUTPUT_DIR="patched_apk"

# 1. Decompile APK
apktool d "$APK_FILE" -o "$OUTPUT_DIR"

# 2. Modify network_security_config.xml
NSC_FILE="$OUTPUT_DIR/res/xml/network_security_config.xml"
if [ -f "$NSC_FILE" ]; then
    cat > "$NSC_FILE" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </base-config>
</network-security-config>
EOF
    echo "[+] Modified network_security_config.xml"
fi

# 3. Remove certificate pinning from smali code
find "$OUTPUT_DIR" -name "*.smali" -exec grep -l "CertificatePinner" {} \; | while read file; do
    echo "[*] Processing: $file"
    # Patch CertificatePinner.check to return immediately
    sed -i 's/invoke-virtual.*CertificatePinner.*check/return-void\n# Patched: &/g' "$file"
done

# 4. Remove pinned certificates from assets
rm -rf "$OUTPUT_DIR/assets/certificates" 2>/dev/null
rm -rf "$OUTPUT_DIR/res/raw/"*cert* 2>/dev/null
rm -rf "$OUTPUT_DIR/res/raw/"*pin* 2>/dev/null

# 5. Modify AndroidManifest.xml to allow backup and debugging
MANIFEST="$OUTPUT_DIR/AndroidManifest.xml"
sed -i 's/android:allowBackup="false"/android:allowBackup="true"/g' "$MANIFEST"
sed -i 's/android:debuggable="false"/android:debuggable="true"/g' "$MANIFEST"

# 6. Rebuild APK
apktool b "$OUTPUT_DIR" -o "${APK_FILE%.apk}_patched.apk"

# 7. Sign APK
keytool -genkey -v -keystore debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" 2>/dev/null

jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore debug.keystore -storepass android "${APK_FILE%.apk}_patched.apk" androiddebugkey

# 8. Align APK
zipalign -v 4 "${APK_FILE%.apk}_patched.apk" "${APK_FILE%.apk}_patched_aligned.apk"

echo "[+] Patched APK: ${APK_FILE%.apk}_patched_aligned.apk"
```

---

