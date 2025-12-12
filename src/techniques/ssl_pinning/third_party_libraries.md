## 11. Third-Party Libraries

### 11.1 TrustKit

TrustKit is a popular open-source library for SSL pinning.

#### Implementation

```java
// Application.java
public class MyApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        
        // Initialize TrustKit
        TrustKit.initializeWithNetworkSecurityConfiguration(this);
        
        // Or with programmatic configuration
        HashSet<String> pins = new HashSet<>();
        pins.add("sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=");
        pins.add("sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=");
        
        TrustKit.Builder builder = new TrustKit.Builder(this)
            .addPublicKeyHasher(PublicKeyHasher.SHA256)
            .shouldReportPinningFailures(true)
            .reportUris(new String[]{"https://report.example.com/pin"});
        
        builder.domain("api.example.com")
            .publicKeyHashes(pins)
            .enforcePinning(true)
            .includeSubdomains(true);
        
        builder.build();
    }
}

// Usage with OkHttp
OkHttpClient client = new OkHttpClient.Builder()
    .sslSocketFactory(
        TrustKit.getInstance().getSSLSocketFactory("api.example.com"),
        TrustKit.getInstance().getTrustManager("api.example.com")
    )
    .build();
```

#### Bypass

```javascript
Java.perform(function() {
    try {
        var TrustKit = Java.use('com.datatheorem.android.trustkit.TrustKit');
        var PinningTrustManager = Java.use(
            'com.datatheorem.android.trustkit.pinning.PinningTrustManager'
        );
        
        // Bypass the TrustManager
        PinningTrustManager.checkServerTrusted.overload(
            '[Ljava.security.cert.X509Certificate;',
            'java.lang.String'
        ).implementation = function(chain, authType) {
            console.log('[+] TrustKit pinning bypassed');
        };
        
        // Also bypass OkHostnameVerifier
        var OkHostnameVerifier = Java.use(
            'com.datatheorem.android.trustkit.pinning.OkHostnameVerifier'
        );
        
        OkHostnameVerifier.verify.overload(
            'java.lang.String',
            'javax.net.ssl.SSLSession'
        ).implementation = function(hostname, session) {
            console.log('[+] TrustKit hostname verification bypassed');
            return true;
        };
        
    } catch(e) {
        console.log('[-] TrustKit bypass failed: ' + e);
    }
});
```

### 11.2 Retrofit + OkHttp

Already covered in the OkHttp section, but here's a complete example:

```kotlin
// Retrofit with pinning
object ApiClient {
    private const val BASE_URL = "https://api.example.com/"
    
    private val certificatePinner = CertificatePinner.Builder()
        .add("api.example.com", "sha256/...")
        .add("api.example.com", "sha256/...") // Backup
        .build()
    
    private val okHttpClient = OkHttpClient.Builder()
        .certificatePinner(certificatePinner)
        .addInterceptor(HttpLoggingInterceptor())
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
```

### 11.3 Volley

```java
// Custom HurlStack with pinning
public class PinnedHurlStack extends HurlStack {
    
    private final SSLSocketFactory sslSocketFactory;
    
    public PinnedHurlStack() {
        try {
            TrustManagerFactory tmf = TrustManagerFactory.getInstance(
                TrustManagerFactory.getDefaultAlgorithm()
            );
            
            // Load pinned certificate
            CertificateFactory cf = CertificateFactory.getInstance("X.509");
            InputStream caInput = getContext().getResources()
                .openRawResource(R.raw.pinned_cert);
            Certificate ca = cf.generateCertificate(caInput);
            
            KeyStore keyStore = KeyStore.getInstance(KeyStore.getDefaultType());
            keyStore.load(null, null);
            keyStore.setCertificateEntry("ca", ca);
            
            tmf.init(keyStore);
            
            SSLContext sslContext = SSLContext.getInstance("TLS");
            sslContext.init(null, tmf.getTrustManagers(), null);
            
            sslSocketFactory = sslContext.getSocketFactory();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
    
    @Override
    protected HttpURLConnection createConnection(URL url) throws IOException {
        HttpURLConnection connection = super.createConnection(url);
        
        if (connection instanceof HttpsURLConnection) {
            ((HttpsURLConnection) connection)
                .setSSLSocketFactory(sslSocketFactory);
        }
        
        return connection;
    }
}

// Usage
RequestQueue queue = Volley.newRequestQueue(context, new PinnedHurlStack());
```

#### Volley Bypass

```javascript
Java.perform(function() {
    // Hook HurlStack
    try {
        var HurlStack = Java.use('com.android.volley.toolbox.HurlStack');
        
        HurlStack.createConnection.implementation = function(url) {
            var connection = this.createConnection(url);
            console.log('[+] Volley connection created for: ' + url);
            
            // Remove SSL socket factory customization
            if (connection.getClass().getName().includes('HttpsURLConnection')) {
                // Connection will use default (non-pinned) SSL
            }
            
            return connection;
        };
    } catch(e) {
        console.log('[-] HurlStack hook failed: ' + e);
    }
});
```

---

