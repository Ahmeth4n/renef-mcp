# SSL Pinning Documentation Structure

This directory contains modular SSL/TLS Certificate Pinning documentation organized by platform and content type.

## 📁 File Structure

### Original Complete Documentation
- **`DOC.md`** (3200 lines) - Complete original documentation containing all platforms

### Common Sections (Shared Across All Platforms)
These sections provide foundational knowledge applicable to all platforms:

| File | Lines | Description |
|------|-------|-------------|
| `introduction_to_ssl_pinning.md` | 27 | What is SSL pinning, why it's used, types of pinning |
| `how_ssl_tls_works.md` | 65 | TLS handshake, certificate chain validation |
| `certificate_pinning_fundamentals.md` | 50 | What gets pinned, extracting pin values |
| `third_party_libraries.md` | 191 | OkHttp, Retrofit, Volley, etc. |
| `advanced_bypass_techniques.md` | 309 | Frida / Renef scripts, hooking techniques |
| `detection_anti_tampering.md` | 158 | Root/jailbreak detection, anti-tampering |
| `summary.md` | 33 | Summary and best practices |

### Android-Specific Common Section
| File | Lines | Description |
|------|-------|-------------|
| `network_security_configuration.md` | 190 | Android Network Security Config (API 24+) |

### Platform-Specific Sections
Each platform file contains ONLY the implementation details specific to that platform:

| File | Lines | Platform | Description |
|------|-------|----------|-------------|
| `android_native.md` | 610 | Android | Java/Kotlin TrustManager, OkHttp, Retrofit implementations |
| `flutter.md` | 518 | Flutter | Dart HttpClient, http package, certificate pinning |
| `react_native.md` | 329 | React Native | JavaScript SSL pinning libraries and native bridges |
| `xamarin.md` | 246 | Xamarin | C# ServicePointManager, HttpClientHandler |
| `cordova_ionic.md` | 192 | Cordova/Ionic | Cordova plugins, advanced-http configuration |
| `unity.md` | 262 | Unity | UnityWebRequest, CertificateHandler, C# implementation |

## 🎯 Usage by MCP Server

The `platform_mapping.json` file defines which files to combine for each platform:

```json
{
  "platforms": {
    "android_native": {
      "files": [
        "introduction_to_ssl_pinning.md",
        "how_ssl_tls_works.md",
        "certificate_pinning_fundamentals.md",
        "android_native.md",
        "network_security_configuration.md",
        "third_party_libraries.md",
        "advanced_bypass_techniques.md",
        "detection_anti_tampering.md",
        "summary.md"
      ]
    }
  }
}
```

### Example Workflow

1. **Platform Detection**: MCP server detects the app is built with Flutter
2. **File Lookup**: Checks `platform_mapping.json` → finds `flutter` key
3. **File Retrieval**: Reads the files listed in the `files` array
4. **Concatenation**: Combines them in order:
   - Introduction
   - How SSL/TLS Works
   - Certificate Pinning Fundamentals
   - **Flutter-specific implementation** (flutter.md)
   - Network Security Configuration
   - Third-Party Libraries
   - Advanced Bypass Techniques
   - Detection and Anti-Tampering
   - Summary
5. **Response**: Returns the complete, platform-specific documentation

## 🔍 Platform Detection Keywords

Each platform in `platform_mapping.json` includes detection keywords:

- **Android Native**: `TrustManager`, `OkHttp`, `javax.net.ssl`
- **Flutter**: `libflutter.so`, `dart:io`, `pubspec.yaml`
- **React Native**: `react-native`, `libreactnativejni`, `metro`
- **Xamarin**: `Xamarin`, `mono`, `ServicePointManager`
- **Cordova/Ionic**: `cordova`, `ionic`, `config.xml`
- **Unity**: `unity`, `il2cpp`, `UnityWebRequest`

## 📊 Content Distribution

```
Total Lines: 3200

Common sections (all platforms): 893 lines
  ├─ Introduction: 27
  ├─ How SSL/TLS Works: 65
  ├─ Fundamentals: 50
  ├─ Third-Party Libraries: 191
  ├─ Advanced Bypass: 309
  ├─ Detection: 158
  └─ Summary: 33

Android-specific common: 190 lines
  └─ Network Security Config: 190

Platform-specific content: 2157 lines
  ├─ Android Native: 610
  ├─ Flutter: 518
  ├─ React Native: 329
  ├─ Xamarin: 246
  ├─ Cordova/Ionic: 192
  └─ Unity: 262
```

## ✅ Benefits of This Structure

1. **No Duplication**: Common sections aren't repeated in every platform file
2. **Modularity**: Easy to update a specific section without touching others
3. **Flexibility**: MCP server can mix and match sections as needed
4. **Maintainability**: Changes to common techniques apply to all platforms
5. **Efficiency**: Smaller file sizes for platform-specific content
6. **Clarity**: Each file has a single, clear purpose

## 🔧 Maintenance

To update documentation:

1. **Common content**: Edit the shared `.md` files
2. **Platform-specific**: Edit the platform's `.md` file
3. **New platform**:
   - Create new `platform_name.md` file
   - Add entry to `platform_mapping.json`
4. **Regenerate full docs**: Concatenate files as specified in mapping

## 📝 Notes

- Original `DOC.md` is preserved for reference
- All 3200 lines are accounted for across the modular files
- No content was lost during the split
- Files are named using snake_case for consistency
