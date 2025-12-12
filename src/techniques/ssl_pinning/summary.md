## Summary

### Quick Reference: Platform-Specific Bypass

| Platform | Primary Method | Key Classes/Functions |
|----------|---------------|----------------------|
| **Native Java/Kotlin** | TrustManager hook | `X509TrustManager.checkServerTrusted()` |
| **OkHttp** | CertificatePinner hook | `CertificatePinner.check()` |
| **Network Security Config** | XML modification or hook | `NetworkSecurityTrustManager` |
| **Flutter** | Native lib hook | `ssl_crypto_x509_session_verify_cert_chain` in `libflutter.so` |
| **React Native** | OkHttp bypass | Same as OkHttp + plugin-specific |
| **Xamarin** | Mono/Native hook | `ServicePointManager.ServerCertificateValidationCallback` |
| **Cordova/Ionic** | Plugin + WebView hook | Plugin-specific + `WebViewClient.onReceivedSslError()` |
| **Unity** | IL2CPP/Mono hook | `CertificateHandler.ValidateCertificate()` |

### Tools Required

1. **Renef** - Dynamic instrumentation
2. **Frida / Renef** - Dynamic instrumentation
3. **objection** - Frida / Renef-based automation
4. **apktool** - APK decompilation
5. **jadx** - Java decompilation
6. **Ghidra/IDA** - Binary analysis (for native libs)
7. **Burp Suite/mitmproxy** - Traffic interception

### Best Practices for Security Researchers

1. Always document which methods you tried
2. Start with universal bypass, then move to specific
3. Check for multiple layers of pinning
4. Monitor logcat for clues about pinning implementation
5. Use both runtime (Frida / Renef) and static (patching) approaches
6. Keep bypass scripts updated for new library versions

