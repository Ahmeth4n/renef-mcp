# Renef MCP Server

MCP server for Renef - Dynamic instrumentation toolkit for Android ARM64 reverse engineering and security analysis.

## Features

- Native function hooking (PLT/GOT and trampoline methods)
- Java/JNI method interception
- Memory read/write operations
- Runtime patching and code injection
- Module and symbol inspection
- SSL/TLS pinning bypass techniques
- Framework detection (Flutter, React Native, Unity, Xamarin)
- Comprehensive technique documentation

## Installation

```bash
pip install renef-mcp
```

### Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "renef": {
      "command": "renef-mcp"
    }
  }
}
```


## Documentation

- Homepage: https://renef.io
- Repository: https://github.com/ahmeth4n/renef
- Issues: https://github.com/ahmeth4n/renef/issues

## License

MIT License - Copyright (c) 2025 Byteria
