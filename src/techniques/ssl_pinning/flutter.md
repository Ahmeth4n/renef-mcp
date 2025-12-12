## 5. Flutter

Flutter uses its own SSL implementation bundled in `libflutter.so`, which is compiled from BoringSSL (Google's fork of OpenSSL). This makes bypassing more complex as it doesn't use Android's Java SSL classes.

### 5.1 How Flutter SSL Works

```
┌─────────────────────────────────────────────────────────────┐
│                      Dart Code                               │
│   HttpClient / http package / dio                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    dart:io (HttpClient)                      │
│              _SecureSocket implementation                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     libflutter.so                            │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   BoringSSL                          │   │
│   │                                                      │   │
│   │  ssl_crypto_x509_session_verify_cert_chain()        │   │
│   │          ↓                                          │   │
│   │  Verifies certificate chain                         │   │
│   │  Returns: 1 (success) or 0 (failure)                │   │
│   │                                                      │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Flutter Pinning Implementations

#### Method 1: Using SecurityContext (Dart)

```dart
import 'dart:io';

class PinnedHttpClient {
  static const String pinnedCertPem = '''
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
... (certificate content)
-----END CERTIFICATE-----
''';

  static HttpClient createPinnedClient() {
    final securityContext = SecurityContext(withTrustedRoots: false);
    
    // Add pinned certificate
    securityContext.setTrustedCertificatesBytes(
      pinnedCertPem.codeUnits,
    );
    
    final client = HttpClient(context: securityContext);
    
    // Optional: Custom hostname verification
    client.badCertificateCallback = (cert, host, port) {
      // Implement additional verification
      return false; // Reject bad certificates
    };
    
    return client;
  }
}

// Usage with http package
class ApiClient {
  final HttpClient _httpClient = PinnedHttpClient.createPinnedClient();
  
  Future<String> fetchData(String url) async {
    final request = await _httpClient.getUrl(Uri.parse(url));
    final response = await request.close();
    return await response.transform(utf8.decoder).join();
  }
}
```

#### Method 2: Using dio Package with Pinning

```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:dio/io.dart';

class PinnedDioClient {
  static const List<String> pinnedCertificates = [
    '-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
    '-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
  ];
  
  static Dio createPinnedDio() {
    final dio = Dio();
    
    (dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
      final securityContext = SecurityContext(withTrustedRoots: false);
      
      for (final cert in pinnedCertificates) {
        securityContext.setTrustedCertificatesBytes(cert.codeUnits);
      }
      
      final client = HttpClient(context: securityContext);
      client.badCertificateCallback = (cert, host, port) => false;
      
      return client;
    };
    
    return dio;
  }
}
```

#### Method 3: Using http_certificate_pinning Package

```dart
import 'package:http_certificate_pinning/http_certificate_pinning.dart';

class ApiService {
  static const List<String> allowedSHAFingerprints = [
    'AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA:AA',
    'BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB:BB',
  ];
  
  Future<String> secureRequest(String url) async {
    try {
      final response = await HttpCertificatePinning.check(
        serverURL: url,
        headerHttp: {},
        sha: SHA.SHA256,
        allowedSHAFingerprints: allowedSHAFingerprints,
        timeout: 60,
      );
      
      if (response.body != null) {
        return response.body!;
      }
    } on PlatformException catch (e) {
      // Certificate pinning failed
      throw Exception('SSL Pinning Error: ${e.message}');
    }
    
    throw Exception('Request failed');
  }
}
```

#### Method 4: Native Channel Pinning

```dart
// Dart side
class NativePinningChannel {
  static const platform = MethodChannel('com.example.app/ssl_pinning');
  
  static Future<String> makeSecureRequest(String url) async {
    try {
      final result = await platform.invokeMethod('secureRequest', {
        'url': url,
        'pins': [
          'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
          'sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=',
        ],
      });
      return result;
    } on PlatformException catch (e) {
      throw Exception('Pinning failed: ${e.message}');
    }
  }
}
```

```kotlin
// Android native side (Kotlin)
class SslPinningPlugin : FlutterPlugin, MethodCallHandler {
    private lateinit var channel: MethodChannel
    
    override fun onAttachedToEngine(binding: FlutterPluginBinding) {
        channel = MethodChannel(binding.binaryMessenger, "com.example.app/ssl_pinning")
        channel.setMethodCallHandler(this)
    }
    
    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        if (call.method == "secureRequest") {
            val url = call.argument<String>("url")!!
            val pins = call.argument<List<String>>("pins")!!
            
            try {
                val response = makeSecureRequest(url, pins)
                result.success(response)
            } catch (e: Exception) {
                result.error("SSL_ERROR", e.message, null)
            }
        }
    }
    
    private fun makeSecureRequest(url: String, pins: List<String>): String {
        val certificatePinner = CertificatePinner.Builder().apply {
            val host = URL(url).host
            pins.forEach { pin -> add(host, pin) }
        }.build()
        
        val client = OkHttpClient.Builder()
            .certificatePinner(certificatePinner)
            .build()
        
        val request = Request.Builder().url(url).build()
        return client.newCall(request).execute().body?.string() ?: ""
    }
}
```

### 5.3 Flutter Bypass Techniques

#### Method 1: Hook BoringSSL in libflutter.so (Frida / Renef + Native Hooking)

```javascript
// Universal Flutter SSL Bypass
// Works by hooking the native BoringSSL verification function

function findFlutterSSLVerify() {
    // Find libflutter.so
    var modules = Process.enumerateModules();
    var flutter = null;
    
    for (var i = 0; i < modules.length; i++) {
        if (modules[i].name.includes('libflutter.so')) {
            flutter = modules[i];
            break;
        }
    }
    
    if (!flutter) {
        console.log('[-] libflutter.so not found');
        return null;
    }
    
    console.log('[+] libflutter.so found at: ' + flutter.base);
    
    // Search for ssl_crypto_x509_session_verify_cert_chain signature
    // This function returns 1 for success, 0 for failure
    
    // Pattern for ARM64 (common in recent Flutter versions)
    // The exact offset varies by Flutter version
    var patterns = [
        // Pattern 1: Common in Flutter 3.x
        'FF 83 01 D1 FD 7B 02 A9 FD 83 00 91',
        // Pattern 2: Alternative signature
        'F5 0F 1D F8 F4 4F 01 A9 FD 7B 02 A9',
    ];
    
    for (var p = 0; p < patterns.length; p++) {
        var matches = Memory.scanSync(flutter.base, flutter.size, patterns[p]);
        if (matches.length > 0) {
            console.log('[+] Found SSL verify function at: ' + matches[0].address);
            return matches[0].address;
        }
    }
    
    return null;
}

function bypassFlutterSSL() {
    var sslVerifyAddr = findFlutterSSLVerify();
    
    if (sslVerifyAddr) {
        // Hook the function to always return 1 (success)
        Interceptor.attach(sslVerifyAddr, {
            onLeave: function(retval) {
                console.log('[*] SSL verification called, forcing success');
                retval.replace(0x1);
            }
        });
    } else {
        console.log('[!] Trying alternative bypass method...');
        alternativeFlutterBypass();
    }
}

function alternativeFlutterBypass() {
    // Hook Dart's SecurityContext if native hook fails
    Java.perform(function() {
        try {
            // Some Flutter apps use platform channels for additional verification
            var MethodChannel = Java.use('io.flutter.plugin.common.MethodChannel');
            
            MethodChannel.invokeMethod.overload(
                'java.lang.String',
                'java.lang.Object',
                'io.flutter.plugin.common.MethodChannel$Result'
            ).implementation = function(method, args, result) {
                if (method.includes('ssl') || method.includes('certificate') || 
                    method.includes('pin')) {
                    console.log('[*] Intercepted SSL-related method channel: ' + method);
                    result.success(true);
                    return;
                }
                return this.invokeMethod(method, args, result);
            };
        } catch(e) {}
    });
}

// Execute bypass
setTimeout(bypassFlutterSSL, 1000);
```

#### Method 2: Hardcoded Offset Bypass (Version-Specific)

```javascript
// Flutter SSL Bypass with known offsets
// NOTE: Offsets change with each Flutter version!

var FLUTTER_SSL_OFFSETS = {
    // Flutter version: ssl_crypto_x509_session_verify_cert_chain offset
    '3.16.0': 0x5dc730,
    '3.13.0': 0x5d2f80,
    '3.10.0': 0x5c8a40,
    '3.7.0':  0x5b4c20,
    '3.3.0':  0x599800,
    // Add more versions as needed
};

function bypassWithOffset(offset) {
    var modules = Process.enumerateModules();
    
    for (var i = 0; i < modules.length; i++) {
        if (modules[i].name.includes('libflutter.so')) {
            var targetAddr = modules[i].base.add(offset);
            
            console.log('[+] Hooking at: ' + targetAddr);
            
            Interceptor.attach(targetAddr, {
                onEnter: function(args) {
                    console.log('[*] SSL verify called');
                },
                onLeave: function(retval) {
                    retval.replace(0x1); // Always return success
                }
            });
            
            return true;
        }
    }
    return false;
}

// Try multiple offsets
for (var version in FLUTTER_SSL_OFFSETS) {
    if (bypassWithOffset(FLUTTER_SSL_OFFSETS[version])) {
        console.log('[+] Bypass successful with offset for Flutter ' + version);
        break;
    }
}
```

#### Method 3: Patch libflutter.so Binary

```python
#!/usr/bin/env python3
"""
Flutter SSL Pinning Patcher
Patches libflutter.so to bypass SSL verification
"""

import sys
import re

def find_and_patch(data):
    # ARM64 pattern for ssl_crypto_x509_session_verify_cert_chain return
    # MOV W0, #0 followed by RET
    # We change MOV W0, #0 to MOV W0, #1
    
    patterns = [
        # Pattern: MOV W0, #0 (0x52800000) before RET
        (b'\x00\x00\x80\x52', b'\x20\x00\x80\x52'),  # MOV W0, #0 -> MOV W0, #1
    ]
    
    patched = False
    result = bytearray(data)
    
    for original, replacement in patterns:
        # Find all occurrences
        for match in re.finditer(re.escape(original), data):
            offset = match.start()
            # Check if followed by RET (0xD65F03C0) within 16 bytes
            nearby = data[offset:offset+16]
            if b'\xC0\x03\x5F\xD6' in nearby:
                result[offset:offset+len(replacement)] = replacement
                patched = True
                print(f'[+] Patched at offset: 0x{offset:x}')
    
    return bytes(result), patched

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <input.so> <output.so>')
        sys.exit(1)
    
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    
    patched_data, success = find_and_patch(data)
    
    if success:
        with open(sys.argv[2], 'wb') as f:
            f.write(patched_data)
        print('[+] Patched library saved')
    else:
        print('[-] No patterns found to patch')

if __name__ == '__main__':
    main()
```

#### Method 4: Renef-Based Bypass

```lua
-- Renef Flutter SSL Bypass Script
-- For use with Renef instrumentation toolkit

print("[*] Flutter SSL Pinning Bypass loading...")

local SSL_VERIFY_OFFSET = 0x5dc730  -- Update for your Flutter version
local bypass_installed = false

local function install_ssl_bypass()
    if bypass_installed then return true end
    
    local flutter_base = Module.find("libflutter.so")
    if not flutter_base then return false end
    
    print(string.format("[+] libflutter.so found at: 0x%x", flutter_base))
    print(string.format("[+] Installing hook at offset: 0x%x", SSL_VERIFY_OFFSET))
    
    hook("libflutter.so", SSL_VERIFY_OFFSET, {
        onEnter = function(args)
            print("[*] SSL verify called")
        end,
        onLeave = function(retval)
            print("[*] Bypassing SSL verification, returning 1")
            return 1  -- Success
        end
    })
    
    bypass_installed = true
    print(GREEN .. "[+] Flutter SSL pinning bypass ACTIVE!" .. RESET)
    return true
end

-- Try immediate installation
if install_ssl_bypass() then
    print("[+] Bypass installed on existing libflutter.so")
else
    print("[*] libflutter.so not loaded yet, hooking linker...")
    
    -- Hook dynamic linker to catch library loads
    local linker_symbols = Module.symbols("linker64")
    if linker_symbols then
        for _, sym in ipairs(linker_symbols) do
            if sym.name:find("do_dlopen") then
                hook("linker64", sym.offset, {
                    onEnter = function(args)
                        local path = Memory.readString(args[0])
                        if path and path:find("libflutter") then
                            print("[+] libflutter.so loading: " .. path)
                        end
                    end,
                    onLeave = function(retval)
                        if not bypass_installed then
                            install_ssl_bypass()
                        end
                    end
                })
                print("[+] Linker hook installed")
                break
            end
        end
    end
end
```

### 5.4 Finding Flutter SSL Verification Offset

```bash
#!/bin/bash
# Script to find SSL verification offset in libflutter.so

LIBFLUTTER="$1"

if [ -z "$LIBFLUTTER" ]; then
    echo "Usage: $0 <libflutter.so>"
    exit 1
fi

echo "[*] Analyzing $LIBFLUTTER"

# Method 1: Search for known strings
echo "[*] Searching for SSL-related strings..."
strings -t x "$LIBFLUTTER" | grep -i "ssl\|cert\|verify\|x509"

# Method 2: Search for function patterns using objdump
echo "[*] Searching for ssl_crypto_x509_session_verify_cert_chain..."
aarch64-linux-gnu-objdump -d "$LIBFLUTTER" 2>/dev/null | \
    grep -A 50 "ssl_crypto_x509_session_verify_cert_chain" | head -60

# Method 3: Using nm if symbols are available
echo "[*] Checking for symbols..."
nm -D "$LIBFLUTTER" 2>/dev/null | grep -i ssl

# Method 4: Search for specific byte patterns
echo "[*] Searching for verification function patterns..."
xxd "$LIBFLUTTER" | grep -E "ff83 01d1|f50f 1df8"
```

---

