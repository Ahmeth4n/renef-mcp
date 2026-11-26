from src.app import mcp
from src import tools  # noqa: F401 - auto-registers all MCP tools
from src import resources  # noqa: F401 - auto-registers all MCP resources & prompts


def main():
    """Entry point for the renef-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
