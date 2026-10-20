from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nexus-test")

@mcp.tool()
def ping(value: str) -> dict:
    return {"echo": value, "authority": "NONE"}

@mcp.tool()
def double(value: int) -> dict:
    return {"value": value * 2}

@mcp.tool()
def explode() -> dict:
    raise ValueError("boom")

if __name__ == "__main__":
    mcp.run(transport="stdio")
