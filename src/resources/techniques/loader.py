"""
Technique documentation loader utility.

Provides dynamic discovery and loading of technique documentation
with platform-aware content assembly.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class TechniqueLoader:
    """
    Loader for technique documentation with platform support.

    Discovers technique categories by scanning for platform_mapping.json files,
    loads platform-specific documentation, and handles content concatenation
    with truncation support.
    """

    def __init__(self, techniques_base_path: Path):
        """
        Initialize the loader.

        Args:
            techniques_base_path: Path to the techniques/ directory
        """
        self.base_path = techniques_base_path
        self._category_cache: Optional[Dict[str, dict]] = None

    def discover_categories(self) -> Dict[str, dict]:
        """
        Discover all technique categories.

        Scans the techniques/ directory for subdirectories containing
        a platform_mapping.json file. These are considered valid technique
        categories.

        Returns:
            Dict mapping category names to metadata:
            {
                "category_name": {
                    "path": Path(...),
                    "platforms": {...},
                    "description": "..."
                }
            }
        """
        if self._category_cache is not None:
            return self._category_cache

        categories = {}

        # Scan techniques directory
        for item in self.base_path.iterdir():
            if not item.is_dir():
                continue

            mapping_file = item / "platform_mapping.json"
            if not mapping_file.exists():
                continue

            try:
                with open(mapping_file) as f:
                    mapping = json.load(f)
                    categories[item.name] = {
                        "path": item,
                        "platforms": mapping.get("platforms", {}),
                        "description": mapping.get("description", "")
                    }
            except (json.JSONDecodeError, IOError) as e:
                # Skip invalid categories
                print(f"Warning: Failed to load {mapping_file}: {e}")
                continue

        self._category_cache = categories
        return categories

    def load_platform_mapping(self, category: str) -> dict:
        """
        Load platform_mapping.json for a specific category.

        Args:
            category: Category name (e.g., "ssl_pinning")

        Returns:
            Parsed JSON mapping dictionary

        Raises:
            ValueError: If category doesn't exist
            IOError: If file cannot be read
            json.JSONDecodeError: If JSON is invalid
        """
        categories = self.discover_categories()
        if category not in categories:
            raise ValueError(
                f"Unknown category: {category}. "
                f"Available: {', '.join(categories.keys())}"
            )

        mapping_path = categories[category]["path"] / "platform_mapping.json"
        with open(mapping_path) as f:
            return json.load(f)

    def get_platforms(self, category: str) -> List[str]:
        """
        Get list of valid platforms for a category.

        Args:
            category: Category name

        Returns:
            List of platform keys
        """
        mapping = self.load_platform_mapping(category)
        return list(mapping.get("platforms", {}).keys())

    def normalize_platform(self, platform: str, category: str) -> str:
        """
        Normalize platform name, handling aliases and case-insensitivity.

        Args:
            platform: Platform name (can be alias, any case)
            category: Category name

        Returns:
            Normalized platform key

        Raises:
            ValueError: If platform is invalid after normalization
        """
        # Convert to lowercase and replace hyphens
        platform_lower = platform.lower().replace("-", "_")

        # Platform aliases
        aliases = {
            "android": "android_native",
            "rn": "react_native",
            "reactnative": "react_native",
            "cordova": "cordova_ionic",
            "ionic": "cordova_ionic",
        }

        if platform_lower in aliases:
            platform_lower = aliases[platform_lower]

        # Validate against available platforms
        valid_platforms = self.get_platforms(category)
        if platform_lower not in valid_platforms:
            raise ValueError(
                f"Invalid platform: '{platform}'. "
                f"Valid platforms: {', '.join(valid_platforms)}. "
                f"Aliases: android→android_native, rn→react_native, "
                f"cordova/ionic→cordova_ionic"
            )

        return platform_lower

    def load_document_content(
        self,
        category: str,
        platform: str,
        max_lines: Optional[int] = None
    ) -> Tuple[str, dict]:
        """
        Load and concatenate platform-specific documentation.

        Reads all markdown files specified in the platform_mapping.json
        for the given platform and concatenates them in order.

        Args:
            category: Technique category (e.g., "ssl_pinning")
            platform: Platform key (e.g., "flutter")
            max_lines: Maximum lines to return (truncate if exceeded)

        Returns:
            Tuple of (content, metadata):
            - content: Concatenated markdown content
            - metadata: Dict with platform info, files, truncation status

        Raises:
            ValueError: If category or platform is invalid
        """
        # Normalize platform
        platform_normalized = self.normalize_platform(platform, category)

        # Load mapping
        mapping = self.load_platform_mapping(category)
        platform_data = mapping["platforms"][platform_normalized]

        # Get document path
        category_info = self.discover_categories()[category]
        doc_path = category_info["path"]

        # Get files list
        files = platform_data.get("files", [])

        # Concatenate files
        sections = []
        for filename in files:
            file_path = doc_path / filename

            if not file_path.exists():
                print(f"Warning: File not found: {file_path}")
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    # Add section separator
                    sections.append(f"# File: {filename}\n\n{content}")
            except IOError as e:
                print(f"Warning: Failed to read {file_path}: {e}")
                continue

        # Join sections with separator
        full_content = "\n\n" + ("=" * 80) + "\n\n".join(sections)

        # Build metadata
        metadata = {
            "platform": platform_normalized,
            "platform_name": platform_data.get("name", platform_normalized),
            "files_included": files,
            "file_count": len(files),
            "truncated": False,
            "total_lines": 0
        }

        # Handle truncation
        lines = full_content.split('\n')
        metadata["total_lines"] = len(lines)

        if max_lines and len(lines) > max_lines:
            full_content = '\n'.join(lines[:max_lines])
            metadata.update({
                "truncated": True,
                "showing_lines": max_lines,
                "note": (
                    f"Content truncated. Showing {max_lines} of {len(lines)} lines. "
                    f"Use search_techniques tool to find specific topics."
                )
            })

        return full_content, metadata
