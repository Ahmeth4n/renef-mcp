# Renef MCP Server

![alt text](assets/renef-mcp-logo.png "Title")

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

## Screenshots
<img src="assets/renef-claude.png" width="400">

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
- Repository: https://github.com/ahmeth4n/renef-mcp
- Issues: https://github.com/ahmeth4n/renef-mcp/issues

## License

MIT License - Copyright (c) 2025 Byteria