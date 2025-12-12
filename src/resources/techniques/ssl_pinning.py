"""
SSL Pinning technique documentation resources.

Provides MCP resources for accessing platform-specific SSL pinning
bypass documentation.
"""

from pathlib import Path
from src.app import mcp
from src.resources.techniques.loader import TechniqueLoader


# Initialize loader
TECHNIQUES_DIR = Path(__file__).parent.parent.parent / "techniques"
loader = TechniqueLoader(TECHNIQUES_DIR)

# Truncation limit for large docs
MAX_LINES = 500


@mcp.resource("techniques://ssl_pinning")
async def list_ssl_pinning_platforms() -> str:
    """
    List all available SSL pinning platforms with descriptions.

    Returns structured information about supported platforms including:
    - Platform keys and display names
    - Detection keywords for each platform
    - File structure information
    - Usage instructions and aliases

    URI: techniques://ssl_pinning

    Returns:
        Markdown formatted list of platforms
    """
    try:
        mapping = loader.load_platform_mapping("ssl_pinning")

        result = [
            "# SSL Pinning Documentation - Available Platforms",
            "",
            mapping.get("description", "SSL Pinning bypass techniques by platform"),
            "",
            "## Supported Platforms",
            ""
        ]

        # List each platform
        for platform_key, platform_data in mapping["platforms"].items():
            result.append(f"### {platform_data['name']} (key: `{platform_key}`)")
            result.append("")
            result.append(f"**Files:** {len(platform_data.get('files', []))} documents")

            detection_keywords = platform_data.get('detection_keywords', [])
            if detection_keywords:
                result.append(f"**Detection keywords:** {', '.join(detection_keywords)}")

            result.append("")
            result.append(f"**URI:** `techniques://ssl_pinning/{platform_key}`")
            result.append("")

        # Usage instructions
        result.extend([
            "## Usage",
            "",
            "1. Use `renef_detect_platform` tool to identify your target's platform",
            "2. Request the appropriate resource URI based on detected platform",
            "3. Apply the bypass techniques described in the documentation",
            "",
            "## Platform Aliases",
            "",
            "For convenience, the following aliases are supported:",
            "- `android` → `android_native`",
            "- `rn`, `reactnative` → `react_native`",
            "- `cordova`, `ionic` → `cordova_ionic`",
            "",
            "## Example Workflow",
            "",
            "```",
            "# Detect platform",
            "platform_info = renef_detect_platform()",
            "",
            "# If Flutter detected, get Flutter-specific docs",
            "docs = read_resource('techniques://ssl_pinning/flutter')",
            "",
            "# Or search for specific topics",
            "results = search_techniques('HttpClient', platform='flutter')",
            "```"
        ])

        return "\n".join(result)

    except Exception as e:
        return f"Error listing SSL pinning platforms: {str(e)}"


@mcp.resource("techniques://ssl_pinning/{platform}")
async def get_ssl_pinning_docs(platform: str) -> str:
    """
    Get complete SSL pinning documentation for a specific platform.

    Concatenates all relevant documentation files for the platform including:
    - Introduction and fundamentals
    - Platform-specific implementation details
    - Third-party libraries
    - Advanced bypass techniques
    - Detection and anti-tampering measures
    - Summary and best practices

    The documentation is assembled by concatenating multiple markdown files
    as defined in platform_mapping.json. Large documents are automatically
    truncated to 500 lines with metadata about the truncation.

    Args:
        platform: Platform key (flutter, android_native, react_native, etc.)
                 Case-insensitive, supports aliases

    URI: techniques://ssl_pinning/{platform}

    Examples:
        - techniques://ssl_pinning/flutter
        - techniques://ssl_pinning/android  (resolves to android_native)
        - techniques://ssl_pinning/react_native
        - techniques://ssl_pinning/rn  (alias for react_native)

    Returns:
        Complete concatenated documentation with metadata header
    """
    try:
        # Load document content
        content, metadata = loader.load_document_content(
            category="ssl_pinning",
            platform=platform,
            max_lines=MAX_LINES
        )

        # Build response header with metadata
        header = [
            f"# SSL Pinning - {metadata['platform_name']}",
            "",
            f"**Platform:** {metadata['platform']}",
            f"**Documents included:** {metadata['file_count']} files",
            ""
        ]

        # List included files
        if metadata['files_included']:
            header.append("**Files in this documentation:**")
            for i, filename in enumerate(metadata['files_included'], 1):
                header.append(f"{i}. {filename}")
            header.append("")

        # Add truncation notice if applicable
        if metadata.get("truncated"):
            header.extend([
                "---",
                "",
                f"⚠️  **Note:** {metadata['note']}",
                "",
                f"**Total lines:** {metadata['total_lines']}",
                f"**Showing:** {metadata['showing_lines']} lines",
                "",
                "**To find specific content:**",
                "- Use the `search_techniques` tool to search for keywords",
                "- Example: `search_techniques('OkHttp', platform='flutter')`",
                "",
                "---",
                ""
            ])

        # Add separator before content
        header.append("=" * 80)
        header.append("")

        return "\n".join(header) + content

    except ValueError as e:
        # Invalid platform - provide helpful error
        try:
            platforms = loader.get_platforms("ssl_pinning")
            return (
                f"# Error: Invalid Platform\n\n"
                f"{str(e)}\n\n"
                f"## Valid Platforms\n\n"
                + "\n".join(f"- `{p}`" for p in platforms) +
                "\n\n"
                f"## Aliases\n\n"
                f"- `android` → `android_native`\n"
                f"- `rn`, `reactnative` → `react_native`\n"
                f"- `cordova`, `ionic` → `cordova_ionic`\n"
            )
        except Exception:
            return f"Error: {str(e)}"

    except Exception as e:
        return f"Error loading SSL pinning documentation: {str(e)}"
