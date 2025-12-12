"""
Technique documentation search tool.

Provides full-text search across technique documentation with
regex support, platform filtering, and contextual results.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from src.app import mcp
from src.resources.techniques.loader import TechniqueLoader


# Initialize loader
TECHNIQUES_DIR = Path(__file__).parent.parent.parent / "techniques"
loader = TechniqueLoader(TECHNIQUES_DIR)


@mcp.tool()
async def search_techniques(
    query: str,
    technique: str = "ssl_pinning",
    platform: str = None,
    case_sensitive: bool = False,
    context_lines: int = 2
) -> str:
    """
    Search across technique documentation with optional platform filtering.

    Performs full-text search across all documentation files in a technique
    category, returning matching lines with file context. Supports regex
    patterns for advanced searching.

    Args:
        query: Search term or regex pattern (e.g., "OkHttp", "Trust.*Manager")
        technique: Technique category to search (default: "ssl_pinning")
        platform: Filter to specific platform (optional, e.g., "flutter", "android")
        case_sensitive: Enable case-sensitive search (default: False)
        context_lines: Number of context lines before/after match (default: 2)

    Returns:
        Markdown formatted search results with:
        - File name and line number
        - Matched line
        - Context lines (before/after)
        - Limited to 50 results

    Examples:
        Basic search:
            search_techniques("OkHttp")

        Platform-specific:
            search_techniques("HttpClient", platform="flutter")

        Regex pattern:
            search_techniques("Trust.*Manager", case_sensitive=True)

        With more context:
            search_techniques("frida", context_lines=5)
    """
    try:
        # Validate technique category
        categories = loader.discover_categories()
        if technique not in categories:
            available = ', '.join(categories.keys())
            return (
                f"# Error: Unknown Technique\n\n"
                f"Technique '{technique}' not found.\n\n"
                f"**Available techniques:** {available}\n"
            )

        category_path = categories[technique]["path"]
        mapping = loader.load_platform_mapping(technique)

        # Determine which files to search
        files_to_search: List[str] = []
        search_label = ""

        if platform:
            # Search only platform-specific files
            try:
                platform_normalized = loader.normalize_platform(platform, technique)
                platform_data = mapping["platforms"][platform_normalized]
                files_to_search = platform_data.get("files", [])
                search_label = f"{technique}/{platform_normalized}"
            except ValueError as e:
                return (
                    f"# Error: Invalid Platform\n\n"
                    f"{str(e)}\n"
                )
        else:
            # Search all markdown files in the category
            all_md_files = list(category_path.glob("*.md"))
            files_to_search = [f.name for f in all_md_files]
            search_label = f"{technique}/all platforms"

        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            return (
                f"# Error: Invalid Regex Pattern\n\n"
                f"Failed to compile regex: {str(e)}\n\n"
                f"**Query:** `{query}`\n"
            )

        # Perform search
        results: List[Dict[str, Any]] = []

        for filename in files_to_search:
            file_path = category_path / filename
            if not file_path.exists():
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        # Calculate context bounds
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = lines[start:end]

                        results.append({
                            "file": filename,
                            "line": i + 1,  # 1-indexed
                            "match": line.strip(),
                            "context": "".join(context),
                            "context_start": start + 1
                        })

            except IOError as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                continue

        # Format results
        if not results:
            return (
                f"# Search Results: No Matches\n\n"
                f"**Query:** `{query}`\n"
                f"**Scope:** {search_label}\n"
                f"**Case sensitive:** {case_sensitive}\n\n"
                f"No matches found. Try:\n"
                f"- Broadening your search term\n"
                f"- Checking spelling\n"
                f"- Removing platform filter\n"
                f"- Using regex patterns (e.g., `.*ssl.*`)\n"
            )

        # Build output
        output = [
            f"# Search Results: '{query}'",
            "",
            f"**Scope:** {search_label}",
            f"**Case sensitive:** {case_sensitive}",
            f"**Matches:** {len(results)}",
            ""
        ]

        # Limit to 50 results
        result_limit = 50
        displayed_results = results[:result_limit]

        for i, result in enumerate(displayed_results, 1):
            output.extend([
                f"## Match {i}",
                "",
                f"**File:** `{result['file']}`  ",
                f"**Line:** {result['line']}  ",
                f"**Matched:** `{result['match']}`",
                "",
                "```",
                result['context'].rstrip(),
                "```",
                ""
            ])

        # Add truncation notice if needed
        if len(results) > result_limit:
            output.extend([
                "---",
                "",
                f"**Note:** Showing {result_limit} of {len(results)} results.",
                "",
                "To refine your search:",
                "- Use more specific query terms",
                "- Add platform filter",
                "- Use regex patterns for precise matching",
                ""
            ])

        return "\n".join(output)

    except Exception as e:
        return (
            f"# Search Error\n\n"
            f"An unexpected error occurred: {str(e)}\n"
        )
