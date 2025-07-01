# mcp_client.py
import asyncio
import json
import os
import ollama
from fastmcp import Client, FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    config = {
        "mcpServers": {
            "simple": {
                "command": "python",
                "args": ["server.py"]
            },
            "blender": {
                "command": "uvx",
                "args": [
                    "blender-mcp"
                ]
            }
        }
    }
    os.environ["OPENAI_API_KEY"] = "NA"
    model_name = 'incept5/llama3.1-claude:latest'
    model_name = 'qwen2.5:3b'

    async with Client(config) as client:
        # List resources from all servers
        resources = await client.list_resources()
        print(f"Resources: {[r.name for r in resources]}")
        # List resource templates from all servers
        templates = await client.list_resource_templates()
        print(f"Templates: {[t.name for t in templates]}")

        # List prompts
        prompts = await client.list_prompts()
        print(f"Prompts: {[p.name for p in prompts]}")

        # Read resource via template
        #result = await client.read_resource("file://hello/world")
        result = await client.read_resource("file://simple/hello/Junior")
        print(f"Content: {result}")

"""
        # Get prompt
        prompt_result = await client.get_prompt(
            "simple_greet",
            arguments={"name": "Alice"}
        )
        print(f"Prompt: {prompt_result.messages[0].content.text}")
        # Might not ever run on a CPU
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user',
                'content': f''' Take this prompt and generate an appropriate response: {prompt_result} '''
            }]
        )
        print(f"Generated prompt response: {response}")
"""
if __name__ == "__main__":
    asyncio.run(main())
