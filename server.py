from fastmcp import FastMCP
mcp = FastMCP("Simple Server")
@mcp.resource("file://hello/{name}")
async def hello_resource(name: str):
    """Get a personalized hello message"""
    return f"Hello {name} from MCP resource!"
@mcp.prompt("greet")
async def greet_prompt(name: str = "World"):
    """Generate a greeting prompt"""
    return f"Please greet {name} in a friendly way."
if __name__ == "__main__":
    mcp.run()
