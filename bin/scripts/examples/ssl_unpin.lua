-- SSL Pinning Bypass for Renef
-- written by @ahmeth4n
-- Usage: ./renef -s com.example.app -l scripts/ssl_unpin.lua
--
-- Covers 30+ bypass targets:
--   Java: TrustManagerImpl, OkHttp3, OkHttp2 (Squareup), Trustkit,
--         Conscrypt, Apache, Appcelerator, Fabric, Netty, CWAC-Netsecurity,
--         IBM MobileFirst/WorkLight, PhoneGap, Chromium Cronet,
--         Flutter plugins, WebViewClient, Cordova, Boye
--   Native: OpenSSL/BoringSSL SSL_CTX_set_verify
--   Flutter: libflutter.so pattern-based + offset-based bypass
--
--
__hook_type__ = "trampoline"

print(CYAN .. "=== Renef SSL Pinning Bypass ===" .. RESET)

local bypass_count = 0

local function safe_hook(class, method, sig, callbacks, label)
    local ok, err = pcall(function()
        hook(class, method, sig, callbacks)
    end)
    if ok then
        bypass_count = bypass_count + 1
        print(GREEN .. "  [+] " .. label .. RESET)
    else
        print(YELLOW .. "  [-] " .. label .. " (not found)" .. RESET)
    end
end

--------------------------------------------------------------
-- 1. Android TrustManagerImpl
--    [needs ExceptionClear for full bypass]
--
--    Hook arg layout (instance method):
--      args[0] = ArtMethod*, args[1] = this,
--      args[2] = first Java param, args[3] = second, ...
--------------------------------------------------------------
print("\n[1] TrustManagerImpl...")

-- verifyChain: save untrustedChain arg, return it in onLeave
local _saved_chain = nil
safe_hook(
    "com/android/org/conscrypt/TrustManagerImpl",
    "verifyChain",
    "(Ljava/security/cert/X509Certificate;[Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Z)Ljava/util/List;",
    {
        onEnter = function(args)
            _saved_chain = args[2]  -- untrustedChain (first Java param)
            print("  [*] TrustManagerImpl.verifyChain intercepted")
        end,
        onLeave = function(retval)
            if _saved_chain then return _saved_chain end
            return retval.raw
        end
    },
    "TrustManagerImpl.verifyChain (sig1)"
)

-- Alternative signature (Android 7+)
local _saved_chain2 = nil
safe_hook(
    "com/android/org/conscrypt/TrustManagerImpl",
    "verifyChain",
    "([Ljava/security/cert/X509Certificate;[B[BLjava/lang/String;Z)Ljava/util/List;",
    {
        onEnter = function(args)
            _saved_chain2 = args[2]
            print("  [*] TrustManagerImpl.verifyChain intercepted (sig2)")
        end,
        onLeave = function(retval)
            if _saved_chain2 then return _saved_chain2 end
            return retval.raw
        end
    },
    "TrustManagerImpl.verifyChain (sig2)"
)

-- checkTrustedRecursive
safe_hook(
    "com/android/org/conscrypt/TrustManagerImpl",
    "checkTrustedRecursive",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/security/cert/X509Certificate;Z[B[BLjava/util/ArrayList;)Ljava/util/ArrayList;",
    {
        onEnter = function(args)
            print("  [*] TrustManagerImpl.checkTrustedRecursive intercepted")
        end,
        onLeave = function(retval)
            return retval.raw
        end
    },
    "TrustManagerImpl.checkTrustedRecursive"
)

--------------------------------------------------------------
-- 2. OkHttp3 CertificatePinner
--    [needs ExceptionClear - throws SSLPeerUnverifiedException]
--------------------------------------------------------------
print("\n[2] OkHttp3 CertificatePinner...")

safe_hook(
    "okhttp3/CertificatePinner",
    "check",
    "(Ljava/lang/String;Ljava/util/List;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OkHttp3 CertificatePinner.check bypassed")
        end
    },
    "CertificatePinner.check(String, List)"
)

safe_hook(
    "okhttp3/CertificatePinner",
    "check",
    "(Ljava/lang/String;Lkotlin/jvm/functions/Function0;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OkHttp3 CertificatePinner.check (Kotlin) bypassed")
        end
    },
    "CertificatePinner.check(String, Function0)"
)

-- check$okhttp variant (proguarded/internal)
safe_hook(
    "okhttp3/CertificatePinner",
    "check$okhttp",
    "(Ljava/lang/String;Lkotlin/jvm/functions/Function0;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OkHttp3 CertificatePinner.check$okhttp bypassed")
        end
    },
    "CertificatePinner.check$okhttp"
)

safe_hook(
    "okhttp3/CertificatePinner",
    "check",
    "(Ljava/lang/String;[Ljava/security/cert/Certificate;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OkHttp3 CertificatePinner.check(Certificate[]) bypassed")
        end
    },
    "CertificatePinner.check(String, Certificate[])"
)

--------------------------------------------------------------
-- 3. OkHttp3 OkHostnameVerifier (boolean return - works)
--------------------------------------------------------------
print("\n[3] OkHttp3 HostnameVerifier...")

safe_hook(
    "okhttp3/internal/tls/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z",
    {
        onLeave = function(retval)
            print("  [*] OkHostnameVerifier.verify(SSLSession) -> true")
            return 1
        end
    },
    "OkHostnameVerifier.verify(String, SSLSession)"
)

safe_hook(
    "okhttp3/internal/tls/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljava/security/cert/X509Certificate;)Z",
    {
        onLeave = function(retval)
            print("  [*] OkHostnameVerifier.verify(cert) -> true")
            return 1
        end
    },
    "OkHostnameVerifier.verify(String, X509Certificate)"
)

--------------------------------------------------------------
-- 4. Trustkit
--------------------------------------------------------------
print("\n[4] Trustkit...")

safe_hook(
    "com/datatheorem/android/trustkit/pinning/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z",
    {
        onLeave = function(retval)
            print("  [*] Trustkit OkHostnameVerifier(SSLSession) -> true")
            return 1
        end
    },
    "Trustkit OkHostnameVerifier(SSLSession)"
)

safe_hook(
    "com/datatheorem/android/trustkit/pinning/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljava/security/cert/X509Certificate;)Z",
    {
        onLeave = function(retval)
            print("  [*] Trustkit OkHostnameVerifier(cert) -> true")
            return 1
        end
    },
    "Trustkit OkHostnameVerifier(X509Certificate)"
)

-- [needs ExceptionClear]
safe_hook(
    "com/datatheorem/android/trustkit/pinning/PinningTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Trustkit PinningTrustManager bypassed")
        end
    },
    "Trustkit PinningTrustManager"
)

--------------------------------------------------------------
-- 5. Squareup OkHttp v2
--------------------------------------------------------------
print("\n[5] Squareup OkHttp v2...")

-- [needs ExceptionClear]
safe_hook(
    "com/squareup/okhttp/CertificatePinner",
    "check",
    "(Ljava/lang/String;Ljava/security/cert/Certificate;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Squareup CertificatePinner(cert) bypassed")
        end
    },
    "Squareup CertificatePinner(Certificate)"
)

safe_hook(
    "com/squareup/okhttp/CertificatePinner",
    "check",
    "(Ljava/lang/String;Ljava/util/List;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Squareup CertificatePinner(list) bypassed")
        end
    },
    "Squareup CertificatePinner(List)"
)

safe_hook(
    "com/squareup/okhttp/internal/tls/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljava/security/cert/X509Certificate;)Z",
    {
        onLeave = function(retval)
            print("  [*] Squareup OkHostnameVerifier(cert) -> true")
            return 1
        end
    },
    "Squareup OkHostnameVerifier(X509Certificate)"
)

safe_hook(
    "com/squareup/okhttp/internal/tls/OkHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z",
    {
        onLeave = function(retval)
            print("  [*] Squareup OkHostnameVerifier(SSLSession) -> true")
            return 1
        end
    },
    "Squareup OkHostnameVerifier(SSLSession)"
)

--------------------------------------------------------------
-- 6. Conscrypt internals
--------------------------------------------------------------
print("\n[6] Conscrypt...")

safe_hook(
    "com/android/org/conscrypt/ConscryptEngine",
    "verifyCertificateChain",
    "([[BLjava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] ConscryptEngine.verifyCertificateChain bypassed (byte[][])")
        end
    },
    "ConscryptEngine.verifyCertificateChain (byte[][])"
)

safe_hook(
    "com/android/org/conscrypt/ConscryptEngine",
    "verifyCertificateChain",
    "([JLjava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] ConscryptEngine.verifyCertificateChain bypassed (long[])")
        end
    },
    "ConscryptEngine.verifyCertificateChain (long[])"
)

safe_hook(
    "com/android/org/conscrypt/Platform",
    "checkServerTrusted",
    "(Ljavax/net/ssl/X509TrustManager;[Ljava/security/cert/X509Certificate;Ljava/lang/String;Lcom/android/org/conscrypt/AbstractConscryptSocket;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Conscrypt Platform.checkServerTrusted(Socket) bypassed")
        end
    },
    "Conscrypt Platform.checkServerTrusted(Socket)"
)

safe_hook(
    "com/android/org/conscrypt/Platform",
    "checkServerTrusted",
    "(Ljavax/net/ssl/X509TrustManager;[Ljava/security/cert/X509Certificate;Ljava/lang/String;Lcom/android/org/conscrypt/ConscryptEngine;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Conscrypt Platform.checkServerTrusted(Engine) bypassed")
        end
    },
    "Conscrypt Platform.checkServerTrusted(Engine)"
)

safe_hook(
    "com/android/org/conscrypt/OpenSSLSocketImpl",
    "verifyCertificateChain",
    "([JLjava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OpenSSLSocketImpl.verifyCertificateChain bypassed")
        end
    },
    "OpenSSLSocketImpl Conscrypt"
)

safe_hook(
    "com/android/org/conscrypt/OpenSSLEngineSocketImpl",
    "verifyCertificateChain",
    "([Ljava/lang/Long;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] OpenSSLEngineSocketImpl.verifyCertificateChain bypassed")
        end
    },
    "OpenSSLEngineSocketImpl Conscrypt"
)

safe_hook(
    "com/android/org/conscrypt/CertPinManager",
    "isChainValid",
    "(Ljava/lang/String;Ljava/util/List;)Z",
    {
        onLeave = function(retval)
            print("  [*] Conscrypt CertPinManager.isChainValid -> true")
            return 1
        end
    },
    "Conscrypt CertPinManager.isChainValid"
)

safe_hook(
    "com/android/org/conscrypt/CertPinManager",
    "checkChainPinning",
    "(Ljava/lang/String;Ljava/util/List;)Z",
    {
        onLeave = function(retval)
            print("  [*] Conscrypt CertPinManager.checkChainPinning -> true")
            return 1
        end
    },
    "Conscrypt CertPinManager.checkChainPinning"
)

--------------------------------------------------------------
-- 6b. Android Network Security Config
--------------------------------------------------------------
print("\n[6b] Network Security Config...")

safe_hook(
    "android/security/net/config/NetworkSecurityTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] NetworkSecurityTrustManager.checkServerTrusted bypassed")
        end
    },
    "NetworkSecurityTrustManager.checkServerTrusted(basic)"
)

safe_hook(
    "android/security/net/config/NetworkSecurityTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/net/Socket;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] NetworkSecurityTrustManager.checkServerTrusted(Socket) bypassed")
        end
    },
    "NetworkSecurityTrustManager.checkServerTrusted(Socket)"
)

safe_hook(
    "android/security/net/config/NetworkSecurityTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljavax/net/ssl/SSLEngine;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] NetworkSecurityTrustManager.checkServerTrusted(SSLEngine) bypassed")
        end
    },
    "NetworkSecurityTrustManager.checkServerTrusted(SSLEngine)"
)

safe_hook(
    "android/security/net/config/RootTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] RootTrustManager.checkServerTrusted bypassed")
        end
    },
    "RootTrustManager.checkServerTrusted(basic)"
)

safe_hook(
    "android/security/net/config/RootTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/net/Socket;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] RootTrustManager.checkServerTrusted(Socket) bypassed")
        end
    },
    "RootTrustManager.checkServerTrusted(Socket)"
)

safe_hook(
    "android/security/net/config/RootTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljavax/net/ssl/SSLEngine;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] RootTrustManager.checkServerTrusted(SSLEngine) bypassed")
        end
    },
    "RootTrustManager.checkServerTrusted(SSLEngine)"
)

--------------------------------------------------------------
-- 7. CWAC-Netsecurity
--------------------------------------------------------------
safe_hook(
    "com/commonsware/cwac/netsecurity/conscrypt/CertPinManager",
    "isChainValid",
    "(Ljava/lang/String;Ljava/util/List;)Z",
    {
        onLeave = function(retval)
            print("  [*] CWAC-Netsecurity CertPinManager -> true")
            return 1
        end
    },
    "CWAC-Netsecurity CertPinManager"
)

--------------------------------------------------------------
-- 8. Apache / Legacy HTTP
--------------------------------------------------------------
print("\n[7] Apache HttpClient (legacy)...")

safe_hook(
    "org/apache/http/conn/ssl/SSLSocketFactory",
    "isSecure",
    "(Ljava/net/Socket;)Z",
    {
        onLeave = function(retval)
            return 1
        end
    },
    "SSLSocketFactory.isSecure"
)

-- [needs ExceptionClear]
safe_hook(
    "org/apache/http/conn/ssl/AbstractVerifier",
    "verify",
    "(Ljava/lang/String;[Ljava/lang/String;[Ljava/lang/String;Z)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Apache AbstractVerifier.verify bypassed")
        end
    },
    "Apache AbstractVerifier.verify"
)

-- Apache Harmony OpenSSLSocketImpl [needs ExceptionClear]
safe_hook(
    "org/apache/harmony/xnet/provider/jsse/OpenSSLSocketImpl",
    "verifyCertificateChain",
    "([[BLjava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Apache Harmony OpenSSLSocketImpl bypassed")
        end
    },
    "Apache Harmony OpenSSLSocketImpl"
)

-- Boye AbstractVerifier [needs ExceptionClear]
safe_hook(
    "ch/boye/httpclientandroidlib/conn/ssl/AbstractVerifier",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSocket;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Boye AbstractVerifier.verify bypassed")
        end
    },
    "Boye AbstractVerifier"
)

--------------------------------------------------------------
-- 9. Trust Managers (3rd party)
--------------------------------------------------------------
print("\n[8] Trust Managers (3rd party)...")

-- Appcelerator Titanium [needs ExceptionClear]
safe_hook(
    "appcelerator/https/PinningTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Titanium PinningTrustManager bypassed")
        end
    },
    "Appcelerator PinningTrustManager"
)

-- Fabric [needs ExceptionClear]
safe_hook(
    "io/fabric/sdk/android/services/network/PinningTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Fabric PinningTrustManager bypassed")
        end
    },
    "Fabric PinningTrustManager"
)

-- Netty [needs ExceptionClear]
safe_hook(
    "io/netty/handler/ssl/util/FingerprintTrustManagerFactory",
    "checkTrusted",
    "(Ljava/lang/String;[Ljava/security/cert/X509Certificate;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Netty FingerprintTrustManagerFactory bypassed")
        end
    },
    "Netty FingerprintTrustManagerFactory"
)

--------------------------------------------------------------
-- 10. WebView
--------------------------------------------------------------
print("\n[9] WebViewClient SSL errors...")

safe_hook(
    "android/webkit/WebViewClient",
    "onReceivedSslError",
    "(Landroid/webkit/WebView;Landroid/webkit/SslErrorHandler;Landroid/net/http/SslError;)V",
    {
        onEnter = function(args)
            -- TODO: call SslErrorHandler.proceed() on args[3]
            print("  [*] WebViewClient.onReceivedSslError intercepted")
        end
    },
    "WebViewClient.onReceivedSslError"
)

safe_hook(
    "android/webkit/WebViewClient",
    "onReceivedError",
    "(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;Landroid/webkit/WebResourceError;)V",
    {
        onEnter = function(args)
            print("  [*] WebViewClient.onReceivedError intercepted")
        end
    },
    "WebViewClient.onReceivedError"
)

-- Cordova WebViewClient
safe_hook(
    "org/apache/cordova/CordovaWebViewClient",
    "onReceivedSslError",
    "(Landroid/webkit/WebView;Landroid/webkit/SslErrorHandler;Landroid/net/http/SslError;)V",
    {
        onEnter = function(args)
            print("  [*] Cordova WebViewClient.onReceivedSslError intercepted")
        end
    },
    "Cordova WebViewClient.onReceivedSslError"
)

--------------------------------------------------------------
-- 11. Enterprise SDKs
--------------------------------------------------------------
print("\n[10] Enterprise SDKs...")

-- IBM MobileFirst
safe_hook(
    "com/worklight/wlclient/api/WLClient",
    "pinTrustedCertificatePublicKey",
    "(Ljava/lang/String;)V",
    {
        onEnter = function(args)
            print("  [*] IBM MobileFirst pinTrustedCertificatePublicKey(String) bypassed")
        end
    },
    "IBM MobileFirst(String)"
)

safe_hook(
    "com/worklight/wlclient/api/WLClient",
    "pinTrustedCertificatePublicKey",
    "([Ljava/lang/String;)V",
    {
        onEnter = function(args)
            print("  [*] IBM MobileFirst pinTrustedCertificatePublicKey(String[]) bypassed")
        end
    },
    "IBM MobileFirst(String[])"
)

-- IBM WorkLight HostNameVerifier
safe_hook(
    "com/worklight/wlclient/certificatepinning/HostNameVerifierWithCertificatePinning",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSocket;)V",
    {
        onEnter = function(args)
            print("  [*] WorkLight HostNameVerifier(SSLSocket) bypassed")
        end
    },
    "WorkLight HostNameVerifier(SSLSocket)"
)

safe_hook(
    "com/worklight/wlclient/certificatepinning/HostNameVerifierWithCertificatePinning",
    "verify",
    "(Ljava/lang/String;Ljava/security/cert/X509Certificate;)V",
    {
        onEnter = function(args)
            print("  [*] WorkLight HostNameVerifier(X509Certificate) bypassed")
        end
    },
    "WorkLight HostNameVerifier(X509Certificate)"
)

safe_hook(
    "com/worklight/wlclient/certificatepinning/HostNameVerifierWithCertificatePinning",
    "verify",
    "(Ljava/lang/String;[Ljava/lang/String;[Ljava/lang/String;)V",
    {
        onEnter = function(args)
            print("  [*] WorkLight HostNameVerifier(String[],String[]) bypassed")
        end
    },
    "WorkLight HostNameVerifier(String[], String[])"
)

safe_hook(
    "com/worklight/wlclient/certificatepinning/HostNameVerifierWithCertificatePinning",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z",
    {
        onLeave = function(retval)
            print("  [*] WorkLight HostNameVerifier(SSLSession) -> true")
            return 1
        end
    },
    "WorkLight HostNameVerifier(SSLSession)"
)

-- Worklight Androidgap
safe_hook(
    "com/worklight/androidgap/plugin/WLCertificatePinningPlugin",
    "execute",
    "(Ljava/lang/String;Lorg/json/JSONArray;Lorg/apache/cordova/CallbackContext;)Z",
    {
        onLeave = function(retval)
            print("  [*] Worklight WLCertificatePinningPlugin -> true")
            return 1
        end
    },
    "Worklight Androidgap WLCertificatePinningPlugin"
)

-- PhoneGap
safe_hook(
    "nl/xservices/plugins/sslCertificateChecker",
    "execute",
    "(Ljava/lang/String;Lorg/json/JSONArray;Lorg/apache/cordova/CallbackContext;)Z",
    {
        onLeave = function(retval)
            print("  [*] PhoneGap sslCertificateChecker -> true")
            return 1
        end
    },
    "PhoneGap sslCertificateChecker"
)

--------------------------------------------------------------
-- 12. Chromium Cronet
--------------------------------------------------------------
print("\n[11] Chromium Cronet...")

-- Modify arg to force bypass for local trust anchors
safe_hook(
    "org/chromium/net/impl/CronetEngineBuilderImpl",
    "enablePublicKeyPinningBypassForLocalTrustAnchors",
    "(Z)Lorg/chromium/net/impl/CronetEngineBuilderImpl;",
    {
        onEnter = function(args)
            args[2] = 1  -- force true (first Java param for instance method)
            print("  [*] Cronet enablePublicKeyPinningBypass -> true")
        end
    },
    "Cronet enablePublicKeyPinningBypass"
)

safe_hook(
    "org/chromium/net/CronetEngine$Builder",
    "enablePublicKeyPinningBypassForLocalTrustAnchors",
    "(Z)Lorg/chromium/net/CronetEngine$Builder;",
    {
        onEnter = function(args)
            args[2] = 1
            print("  [*] CronetEngine.Builder enablePublicKeyPinningBypass -> true")
        end
    },
    "CronetEngine.Builder enablePublicKeyPinningBypass"
)

--------------------------------------------------------------
-- 13. Flutter Java-side plugins
--------------------------------------------------------------
print("\n[12] Flutter Java plugins...")

safe_hook(
    "diefferson/http_certificate_pinning/HttpCertificatePinning",
    "checkConnexion",
    "(Ljava/lang/String;Ljava/util/List;Ljava/util/Map;ILjava/lang/String;)Z",
    {
        onLeave = function(retval)
            print("  [*] Flutter HttpCertificatePinning -> true")
            return 1
        end
    },
    "Flutter HttpCertificatePinning"
)

safe_hook(
    "com/macif/plugin/sslpinningplugin/SslPinningPlugin",
    "checkConnexion",
    "(Ljava/lang/String;Ljava/util/List;Ljava/util/Map;ILjava/lang/String;)Z",
    {
        onLeave = function(retval)
            print("  [*] Flutter SslPinningPlugin -> true")
            return 1
        end
    },
    "Flutter SslPinningPlugin"
)

--------------------------------------------------------------
-- 14. Appmattus Certificate Transparency
--------------------------------------------------------------
print("\n[13] Appmattus Certificate Transparency...")

-- 14a. Hook verifyCertificateTransparency on the base class.
-- All Appmattus verifiers (TrustManager, HostnameVerifier, Interceptor) call this.
-- Returning null (0) makes the Kotlin `is VerificationResult.Failure` check false,
-- so the caller proceeds without throwing.
safe_hook(
    "com/appmattus/certificatetransparency/internal/verifier/CertificateTransparencyBase",
    "verifyCertificateTransparency",
    "(Ljava/lang/String;Ljava/util/List;)Lcom/appmattus/certificatetransparency/VerificationResult;",
    {
        onEnter = function(args)
            args.skip = true
        end,
        onLeave = function(retval)
            print("  [*] Appmattus CT verification bypassed (base)")
            return 0
        end
    },
    "Appmattus CT Base"
)

-- 14b. HostnameVerifier: direct boolean return as fallback
safe_hook(
    "com/appmattus/certificatetransparency/internal/verifier/CertificateTransparencyHostnameVerifier",
    "verify",
    "(Ljava/lang/String;Ljavax/net/ssl/SSLSession;)Z",
    {
        onLeave = function(retval)
            print("  [*] Appmattus CT HostnameVerifier -> true")
            return 1
        end
    },
    "Appmattus CT HostnameVerifier"
)

-- 14c. TrustManager checkServerTrusted (void)
safe_hook(
    "com/appmattus/certificatetransparency/internal/verifier/CertificateTransparencyTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V",
    {
        onEnter = function(args)
            args.skip = true
            print("  [*] Appmattus CertificateTransparencyTrustManager bypassed")
        end
    },
    "Appmattus TrustManager (void)"
)

-- 14d. TrustManager checkServerTrusted (List-returning)
local _ct_Arrays = nil
do
    local ok, arr = pcall(Java.use, "java/util/Arrays")
    if ok then _ct_Arrays = arr end
end

local _ct_list = nil
safe_hook(
    "com/appmattus/certificatetransparency/internal/verifier/CertificateTransparencyTrustManager",
    "checkServerTrusted",
    "([Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/lang/String;)Ljava/util/List;",
    {
        onEnter = function(args)
            if _ct_Arrays then
                local ok, list = pcall(function()
                    return _ct_Arrays:call("asList", "([Ljava/lang/Object;)Ljava/util/List;", args[2])
                end)
                if ok and list then _ct_list = list end
            end
            args.skip = true
            print("  [*] Appmattus CertificateTransparencyTrustManager (List) bypassed")
        end,
        onLeave = function(retval)
            if _ct_list then return _ct_list.raw end
            return 0
        end
    },
    "Appmattus TrustManager (List)"
)

--------------------------------------------------------------
-- 15. Flutter SSL (native - libflutter.so)
--------------------------------------------------------------
print("\n[14] Flutter SSL bypass (native)...")

local flutter_base = Module.find("libflutter.so")
if flutter_base then
    print(string.format("  libflutter.so @ 0x%x", flutter_base))

    local hooked = false

    -- Phase 1: Try known hardcoded offsets (fast)
    local flutter_ssl_offsets = {
        0x5dc730,  -- Flutter 3.x common
        0x5e5730,
        0x5f1730,
        0x673740,
    }

    for _, offset in ipairs(flutter_ssl_offsets) do
        local ok, err = pcall(function()
            hook("libflutter.so", offset, {
                onLeave = function(retval)
                    return 1  -- SSL verify success
                end
            })
        end)
        if ok then
            bypass_count = bypass_count + 1
            print(GREEN .. string.format("  [+] Flutter SSL verify hooked at offset 0x%x", offset) .. RESET)
            hooked = true
            break
        end
    end

    -- Phase 2: Pattern scanning (more robust, covers more versions)
    -- ARM64 patterns for ssl_verify_peer_cert (from NVISO/mixunpin)
    -- Nibble wildcards (F?) converted to full-byte wildcards (??)
    if not hooked then
        print("  Trying pattern scan for ssl_crypto_x509_session_verify_cert_chain...")

        local flutter_patterns = {
            "?? 0F 1C F8 ?? ?? 01 A9 ?? ?? 02 A9 ?? ?? 03 A9 ?? ?? ?? ?? 68 1A 40 F9",
            "?? 43 01 D1 FE 67 01 A9 F8 5F 02 A9 F6 57 03 A9 F4 4F 04 A9 13 00 40 F9 F4 03 00 AA 68 1A 40 F9",
            "FF 43 01 D1 FE 67 01 A9 ?? ?? 06 94 ?? ?? 06 94 68 1A 40 F9 15 15 41 F9 B5 00 00 B4 B6 4A 40 F9",
        }

        for _, pattern in ipairs(flutter_patterns) do
            local ok, results = pcall(function()
                return Memory.scan(pattern, "libflutter.so")
            end)
            if ok and results and #results > 0 then
                local match = results[1]
                local offset = match.offset
                local ok2 = pcall(function()
                    hook("libflutter.so", offset, {
                        onLeave = function(retval)
                            return 1
                        end
                    })
                end)
                if ok2 then
                    bypass_count = bypass_count + 1
                    print(GREEN .. string.format("  [+] Flutter SSL verify found via pattern at offset 0x%x", offset) .. RESET)
                    hooked = true
                    break
                end
            end
        end
    end

    if not hooked then
        print(YELLOW .. "  [-] No Flutter SSL offset matched. Use 'hookgen libflutter.so' to find it." .. RESET)
    end
else
    print(YELLOW .. "  [-] libflutter.so not loaded (not a Flutter app)" .. RESET)

    -- Hook linker to detect late-loaded Flutter
    local linker = Module.find("linker64")
    if linker then
        local symbols = Module.symbols("linker64")
        if symbols then
            for _, sym in ipairs(symbols) do
                if sym.name and sym.name:find("do_dlopen") then
                    local ok = pcall(function()
                        hook("linker64", sym.offset, {
                            onLeave = function()
                                local base = Module.find("libflutter.so")
                                if base then
                                    print(CYAN .. "  [*] libflutter.so loaded! Reload ssl_unpin.lua to hook." .. RESET)
                                end
                            end
                        })
                    end)
                    if ok then
                        print("  [*] Linker hook installed for late-loaded libraries")
                    end
                    break
                end
            end
        end
    end
end

--------------------------------------------------------------
-- 15. Native OpenSSL SSL_CTX_set_verify
--------------------------------------------------------------
print("\n[14] Native OpenSSL bypass...")

local ssl_libs = {"libssl.so", "libboringssl.so"}
for _, lib in ipairs(ssl_libs) do
    local base = Module.find(lib)
    if base then
        local exports = Module.exports(lib)
        if exports then
            for _, exp in ipairs(exports) do
                if exp.name == "SSL_CTX_set_verify" then
                    local ok = pcall(function()
                        hook(lib, exp.offset, {
                            onEnter = function(args)
                                -- Native: args[0]=ctx, args[1]=verify_mode, args[2]=callback
                                args[1] = 0  -- SSL_VERIFY_NONE
                                args[2] = 0  -- NULL callback
                                print("  [*] SSL_CTX_set_verify -> VERIFY_NONE")
                            end
                        })
                    end)
                    if ok then
                        bypass_count = bypass_count + 1
                        print(GREEN .. "  [+] " .. lib .. " SSL_CTX_set_verify hooked" .. RESET)
                    end
                    break
                end
            end
        end
    end
end

--------------------------------------------------------------
-- 16. SSLContext + HttpsURLConnection (via Java.registerClass)
--------------------------------------------------------------
print("\n[15] SSLContext + HttpsURLConnection (registerClass)...")

local trust_all_verifier = nil
local trust_all_tm = nil
local tm_array = nil
local ok_rc = pcall(function()
    trust_all_verifier = Java.registerClass({
        implements = {"javax/net/ssl/HostnameVerifier"},
        methods = {
            verify = function() return true end
        }
    })

    trust_all_tm = Java.registerClass({
        implements = {"javax/net/ssl/X509TrustManager"},
        methods = {
            checkClientTrusted = function() end,
            checkServerTrusted = function() end,
            getAcceptedIssuers = function() return nil end
        }
    })

    tm_array = Java.array("javax/net/ssl/TrustManager", { trust_all_tm })
end)

if ok_rc and trust_all_verifier and tm_array then
    print(GREEN .. "  [+] Trust-all HostnameVerifier created" .. RESET)
    print(GREEN .. "  [+] Trust-all X509TrustManager created" .. RESET)

    local trust_all_factory = nil
    local ok_factory = pcall(function()
        local SSLCtx = Java.use("javax.net.ssl.SSLContext")
        local ctx = SSLCtx:call("getInstance", "(Ljava/lang/String;)Ljavax/net/ssl/SSLContext;", "TLS")
        ctx:call("init", "([Ljavax/net/ssl/KeyManager;[Ljavax/net/ssl/TrustManager;Ljava/security/SecureRandom;)V", nil, tm_array, nil)
        trust_all_factory = ctx:call("getSocketFactory", "()Ljavax/net/ssl/SSLSocketFactory;")
    end)

    if ok_factory and trust_all_factory then
        print(GREEN .. "  [+] Trust-all SSLSocketFactory created" .. RESET)
    end

    safe_hook(
        "javax/net/ssl/SSLContext",
        "init",
        "([Ljavax/net/ssl/KeyManager;[Ljavax/net/ssl/TrustManager;Ljava/security/SecureRandom;)V",
        {
            onEnter = function(args)
                args[3] = tm_array.raw
                print("  [*] SSLContext.init -> trust-all TrustManager injected")
            end
        },
        "SSLContext.init"
    )

    safe_hook(
        "javax/net/ssl/HttpsURLConnection",
        "setDefaultHostnameVerifier",
        "(Ljavax/net/ssl/HostnameVerifier;)V",
        {
            onEnter = function(args)
                args[1] = trust_all_verifier.raw
                print("  [*] HttpsURLConnection.setDefaultHostnameVerifier -> trust-all")
            end
        },
        "HttpsURLConnection.setDefaultHostnameVerifier"
    )

    safe_hook(
        "javax/net/ssl/HttpsURLConnection",
        "setHostnameVerifier",
        "(Ljavax/net/ssl/HostnameVerifier;)V",
        {
            onEnter = function(args)
                args[2] = trust_all_verifier.raw
                print("  [*] HttpsURLConnection.setHostnameVerifier -> trust-all")
            end
        },
        "HttpsURLConnection.setHostnameVerifier"
    )

    safe_hook(
        "javax/net/ssl/HttpsURLConnection",
        "getDefaultHostnameVerifier",
        "()Ljavax/net/ssl/HostnameVerifier;",
        {
            onLeave = function(retval)
                print("  [*] HttpsURLConnection.getDefaultHostnameVerifier -> trust-all")
                return trust_all_verifier.raw
            end
        },
        "HttpsURLConnection.getDefaultHostnameVerifier"
    )

    if trust_all_factory then
        safe_hook(
            "javax/net/ssl/HttpsURLConnection",
            "setSSLSocketFactory",
            "(Ljavax/net/ssl/SSLSocketFactory;)V",
            {
                onEnter = function(args)
                    args[2] = trust_all_factory.raw
                    print("  [*] HttpsURLConnection.setSSLSocketFactory -> trust-all")
                end
            },
            "HttpsURLConnection.setSSLSocketFactory"
        )

        safe_hook(
            "javax/net/ssl/HttpsURLConnection",
            "setDefaultSSLSocketFactory",
            "(Ljavax/net/ssl/SSLSocketFactory;)V",
            {
                onEnter = function(args)
                    args[1] = trust_all_factory.raw
                    print("  [*] HttpsURLConnection.setDefaultSSLSocketFactory -> trust-all")
                end
            },
            "HttpsURLConnection.setDefaultSSLSocketFactory"
        )
    end
else
    print(YELLOW .. "  [-] Java.registerClass/array not available" .. RESET)
end

--------------------------------------------------------------
-- Summary
--------------------------------------------------------------
print(string.format("\n" .. CYAN .. "=== %d bypass(es) active ===" .. RESET, bypass_count))
if bypass_count > 0 then
    print(GREEN .. "SSL pinning bypass loaded. Use 'watch' to monitor." .. RESET)
else
    print(RED .. "No bypasses were installed. Check if the app uses custom pinning." .. RESET)
end
