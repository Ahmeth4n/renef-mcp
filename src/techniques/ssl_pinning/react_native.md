## 6. React Native

React Native uses the native platform's networking stack, but there are several ways SSL pinning is implemented.

### 6.1 How React Native Networking Works

```
┌─────────────────────────────────────────────────────────────┐
│                    JavaScript Code                           │
│   fetch() / axios / XMLHttpRequest                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    React Native Bridge                       │
│              NativeModules.Networking                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Android Native (OkHttp)                        │
│                                                              │
│   NetworkingModule.java                                      │
│          ↓                                                   │
│   OkHttpClientProvider                                       │
│          ↓                                                   │
│   OkHttpClient (with CertificatePinner)                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 React Native Pinning Implementations

#### Method 1: react-native-ssl-pinning Library

```javascript
// JavaScript side
import { fetch } from 'react-native-ssl-pinning';

const pinnedFetch = async (url) => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Pin configuration
      sslPinning: {
        certs: ['cert1', 'cert2'], // Certificate names in assets
      },
      // Or use public key hashes
      pkPinning: true,
      sslPinning: {
        certs: [
          'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
          'sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=',
        ],
      },
    });
    
    return await response.json();
  } catch (error) {
    if (error.message.includes('SSL')) {
      console.error('SSL Pinning Failed!');
    }
    throw error;
  }
};
```

Native Android implementation (from the library):
```java
// OkHttpUtils.java
public class OkHttpUtils {
    public static OkHttpClient.Builder getBuilder(
        ReadableArray certs, 
        boolean pkPinning
    ) {
        OkHttpClient.Builder builder = new OkHttpClient.Builder();
        
        if (pkPinning && certs != null) {
            CertificatePinner.Builder pinnerBuilder = new CertificatePinner.Builder();
            
            for (int i = 0; i < certs.size(); i++) {
                String pin = certs.getString(i);
                pinnerBuilder.add("**", pin); // Pin for all domains
            }
            
            builder.certificatePinner(pinnerBuilder.build());
        }
        
        return builder;
    }
}
```

#### Method 2: TrustKit-RN

```javascript
// trustkit-rn configuration
import TrustKit from 'react-native-trustkit';

TrustKit.initializeWithConfiguration({
  'api.example.com': {
    includeSubdomains: true,
    publicKeyHashes: [
      'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
      'sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=',
    ],
    enforcePinning: true,
    reportUris: ['https://report.example.com/pin-failure'],
  },
});
```

#### Method 3: Custom Native Module

```java
// android/app/src/main/java/com/app/PinnedNetworkModule.java
public class PinnedNetworkModule extends ReactContextBaseJavaModule {
    
    private static final String[] PINS = {
        "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
    };
    
    private final OkHttpClient client;
    
    public PinnedNetworkModule(ReactApplicationContext context) {
        super(context);
        
        CertificatePinner pinner = new CertificatePinner.Builder()
            .add("api.example.com", PINS[0])
            .add("api.example.com", PINS[1])
            .build();
        
        client = new OkHttpClient.Builder()
            .certificatePinner(pinner)
            .build();
    }
    
    @ReactMethod
    public void request(String url, Promise promise) {
        Request request = new Request.Builder()
            .url(url)
            .build();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onResponse(Call call, Response response) {
                try {
                    promise.resolve(response.body().string());
                } catch (IOException e) {
                    promise.reject("ERROR", e.getMessage());
                }
            }
            
            @Override
            public void onFailure(Call call, IOException e) {
                promise.reject("SSL_ERROR", e.getMessage());
            }
        });
    }
}
```

#### Method 4: Modifying OkHttpClientProvider (Patch Approach)

```java
// Replace default OkHttpClientProvider
public class CustomOkHttpClientProvider implements OkHttpClientProvider {
    
    @Override
    public OkHttpClient get() {
        return new OkHttpClient.Builder()
            .certificatePinner(createPinner())
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();
    }
    
    private CertificatePinner createPinner() {
        return new CertificatePinner.Builder()
            .add("*.example.com", "sha256/...")
            .build();
    }
}
```

### 6.3 React Native Bypass Techniques

#### Method 1: Hook OkHttp (Same as Native Android)

```javascript
Java.perform(function() {
    // Standard OkHttp bypass
    var CertificatePinner = Java.use('okhttp3.CertificatePinner');
    
    CertificatePinner.check.overload(
        'java.lang.String',
        'java.util.List'
    ).implementation = function(hostname, peerCertificates) {
        console.log('[*] RN OkHttp pinning bypassed for: ' + hostname);
        return;
    };
    
    // Hook react-native-ssl-pinning specific classes
    try {
        var SslPinningModule = Java.use('com.toyberman.RNSslPinningModule');
        // Hook methods as needed
    } catch(e) {
        console.log('[-] react-native-ssl-pinning not found');
    }
    
    // Hook TrustKit if used
    try {
        var TrustKit = Java.use('com.datatheorem.android.trustkit.TrustKit');
        // Bypass TrustKit validation
    } catch(e) {}
});
```

#### Method 2: Patch JavaScript Bundle

```bash
# Extract React Native bundle
apktool d app.apk -o app_decoded
cd app_decoded/assets

# Find and extract the JS bundle
cat index.android.bundle | grep -o "sslPinning" # Check if pinning exists

# Modify the bundle to disable pinning
# Replace sslPinning configuration with empty/disabled
sed -i 's/sslPinning:\s*{[^}]*}/sslPinning: {}/g' index.android.bundle
sed -i 's/pkPinning:\s*true/pkPinning: false/g' index.android.bundle

# Rebuild APK
cd ../..
apktool b app_decoded -o app_modified.apk
```

#### Method 3: Hook Native Module Registration

```javascript
Java.perform(function() {
    // Hook the NetworkingModule
    var NetworkingModule = Java.use(
        'com.facebook.react.modules.network.NetworkingModule'
    );
    
    // Hook the OkHttpClient getter
    NetworkingModule.mClient.value = createPermissiveClient();
    
    function createPermissiveClient() {
        var OkHttpClient = Java.use('okhttp3.OkHttpClient');
        var Builder = Java.use('okhttp3.OkHttpClient$Builder');
        
        // Create client without pinning
        return Builder.$new().build();
    }
});
```

#### Method 4: Comprehensive React Native Bypass

```javascript
// Complete React Native SSL Bypass
Java.perform(function() {
    console.log('[*] React Native SSL Bypass Starting...');
    
    // 1. Bypass OkHttp CertificatePinner
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        
        CertificatePinner.check.overload(
            'java.lang.String', 'java.util.List'
        ).implementation = function(h, c) {
            console.log('[+] OkHttp pinning bypassed: ' + h);
        };
        
        CertificatePinner.check$okhttp.overload(
            'java.lang.String', 
            'kotlin.jvm.functions.Function0'
        ).implementation = function(h, f) {
            console.log('[+] OkHttp Kotlin pinning bypassed: ' + h);
        };
    } catch(e) {
        console.log('[-] OkHttp bypass failed: ' + e);
    }
    
    // 2. Bypass react-native-ssl-pinning
    try {
        var fetch = Java.use('com.toyberman.Utils.OkHttpUtils');
        fetch.getClient.implementation = function() {
            console.log('[+] react-native-ssl-pinning bypassed');
            var OkHttpClient = Java.use('okhttp3.OkHttpClient');
            return OkHttpClient.$new();
        };
    } catch(e) {}
    
    // 3. Bypass TrustManager implementations
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var TrustManagerImpl = Java.registerClass({
        name: 'com.bypass.TrustManager',
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    // 4. Hook SSLContext initialization
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    SSLContext.init.overload(
        '[Ljavax.net.ssl.KeyManager;',
        '[Ljavax.net.ssl.TrustManager;',
        'java.security.SecureRandom'
    ).implementation = function(km, tm, sr) {
        console.log('[+] SSLContext.init hooked');
        this.init(km, [TrustManagerImpl.$new()], sr);
    };
    
    console.log('[+] React Native SSL Bypass Complete');
});
```

---

