"""MCP Resources for official Renef v0.4.0 pentest recipes (`renef://recipes`)."""

from src.app import mcp
from src.session import RECIPES_DIR


@mcp.resource("renef://recipes")
async def list_recipes_resource() -> str:
    """Overview and index of all bundled Renef v0.4.0 pentest recipes."""
    lines = ["# Renef v0.4.0 Pentest Recipes", ""]
    readme = RECIPES_DIR / "README.md"
    if readme.is_file():
        lines.append(readme.read_text(encoding="utf-8"))
        lines.append("")

    if RECIPES_DIR.is_dir():
        lines.append("## Resource URIs")
        lines.append("")
        for script in sorted(RECIPES_DIR.glob("*.lua")):
            lines.append(f"- `renef://recipes/{script.stem}` (`{script.name}`)")
    return "\n".join(lines)


@mcp.resource("renef://recipes/{name}")
async def get_recipe_resource(name: str) -> str:
    """Read the Lua source code of a bundled Renef v0.4.0 pentest recipe."""
    clean = name.strip()
    if not clean or "/" in clean or "\\" in clean or ".." in clean:
        return f"ERROR: Invalid recipe name: {name!r}"
    if not clean.endswith(".lua"):
        clean += ".lua"

    target = (RECIPES_DIR / clean).resolve()
    if not str(target).startswith(str(RECIPES_DIR.resolve())) or not target.is_file():
        available = (
            ", ".join(f.stem for f in sorted(RECIPES_DIR.glob("*.lua")))
            if RECIPES_DIR.is_dir()
            else "(none)"
        )
        return f"ERROR: Recipe {name!r} not found. Available: {available}"

    return target.read_text(encoding="utf-8")
