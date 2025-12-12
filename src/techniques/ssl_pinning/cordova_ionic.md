## 8. Cordova/Ionic

Cordova and Ionic apps use WebView for rendering and can implement pinning through plugins.

### 8.1 How Cordova/Ionic Networking Works

```
┌─────────────────────────────────────────────────────────────┐
│                    JavaScript Code                           │
│   XMLHttpRequest / fetch / cordova-plugin-advanced-http     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cordova Bridge                            │
│              exec() → Native Plugin                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Native Implementation (Java)                    │
│   WebView requests or OkHttp (for plugins)                  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Cordova/Ionic Pinning Implementations

#### Method 1: cordova-plugin-advanced-http

```javascript
// JavaScript
document.addEventListener('deviceready', function() {
    cordova.plugin.http.setServerTrustMode('pinned', function() {
        console.log('SSL Pinning enabled');
    }, function(error) {
        console.error('Failed to enable pinning:', error);
    });
    
    // Set pinned certificates
    cordova.plugin.http.setSSLCertMode('pinned');
    
    // Make pinned request
    cordova.plugin.http.get('https://api.example.com/data', {}, {},
        function(response) {
            console.log('Success:', response.data);
        },
        function(error) {
            console.error('Error:', error);
        }
    );
});
```

Native implementation (Java):
```java
// CordovaHttpPlugin.java (simplified)
public class CordovaHttpPlugin extends CordovaPlugin {
    
    private OkHttpClient client;
    private String[] pinnedCerts;
    
    @Override
    public boolean execute(String action, JSONArray args, CallbackContext callback) {
        if (action.equals("setSSLCertMode")) {
            String mode = args.getString(0);
            if (mode.equals("pinned")) {
                initPinnedClient();
            }
            return true;
        }
        // ... other actions
    }
    
    private void initPinnedClient() {
        CertificatePinner pinner = new CertificatePinner.Builder()
            .add("api.example.com", "sha256/...")
            .build();
        
        client = new OkHttpClient.Builder()
            .certificatePinner(pinner)
            .build();
    }
}
```

#### Method 2: cordova-plugin-ssl-certificate-checker

```javascript
// Check certificate before making requests
window.plugins.sslCertificateChecker.check(
    function(successMsg) {
        // Certificate is valid, proceed with request
        makeApiCall();
    },
    function(errorMsg) {
        // Certificate check failed
        alert('Security Error: SSL Certificate mismatch!');
    },
    'https://api.example.com',
    'AA BB CC DD EE FF 00 11 22 33 44 55 66 77 88 99 AA BB CC DD' // Fingerprint
);
```

### 8.3 Cordova/Ionic Bypass Techniques

#### Method 1: Hook Plugin Native Code (Frida / Renef)

```javascript
Java.perform(function() {
    // Hook cordova-plugin-advanced-http
    try {
        var CordovaHttpPlugin = Java.use(
            'com.silkimen.cordovahttp.CordovaHttpPlugin'
        );
        
        // Disable SSL mode checking
        CordovaHttpPlugin.setSSLCertMode.implementation = function(mode) {
            console.log('[*] Ignoring SSL cert mode: ' + mode);
            // Don't set pinned mode
        };
    } catch(e) {
        console.log('[-] CordovaHttpPlugin not found');
    }
    
    // Hook certificate checker plugin
    try {
        var SSLCertChecker = Java.use(
            'nl.xservices.plugins.SSLCertificateChecker'
        );
        
        SSLCertChecker.execute.implementation = function(action, args, callback) {
            console.log('[*] SSL Certificate check bypassed');
            // Call success callback
            callback.success('Bypassed');
            return true;
        };
    } catch(e) {}
    
    // Standard OkHttp bypass also works
    var CertificatePinner = Java.use('okhttp3.CertificatePinner');
    CertificatePinner.check.overload(
        'java.lang.String', 'java.util.List'
    ).implementation = function(h, c) {
        console.log('[+] OkHttp pinning bypassed: ' + h);
    };
});
```

#### Method 2: Modify Cordova Configuration

```bash
# Extract and modify config.xml
apktool d app.apk -o app_decoded

# Edit platforms/android/app/src/main/res/xml/config.xml
# Remove or modify SSL pinning preferences

# Also check www/cordova_plugins.js for plugin configurations
```

#### Method 3: Hook WebView SSL (for in-WebView requests)

```javascript
Java.perform(function() {
    var WebViewClient = Java.use('android.webkit.WebViewClient');
    
    WebViewClient.onReceivedSslError.overload(
        'android.webkit.WebView',
        'android.webkit.SslErrorHandler',
        'android.net.http.SslError'
    ).implementation = function(view, handler, error) {
        console.log('[*] WebView SSL error bypassed');
        handler.proceed();
    };
    
    // Hook CordovaWebViewClient if exists
    try {
        var CordovaWebViewClient = Java.use(
            'org.apache.cordova.engine.SystemWebViewClient'
        );
        
        CordovaWebViewClient.onReceivedSslError.implementation = 
            function(view, handler, error) {
                console.log('[*] Cordova WebView SSL bypassed');
                handler.proceed();
            };
    } catch(e) {}
});
```

---

