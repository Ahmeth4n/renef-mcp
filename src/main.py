from src.app import mcp
from src import tools  # Auto-imports all tools
from src import resources  # Auto-imports all resources


def main():
    """Entry point for the renef-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
