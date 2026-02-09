from mcp.server.fastmcp import FastMCP
from datetime import datetime

# 1. Tworzymy serwer
mcp = FastMCP("DateServer")

# 2. Dodajemy narzędzie


@mcp.tool()
async def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

# 3. Uruchamiamy
if __name__ == "__main__":
    mcp.run(transport='stdio')
