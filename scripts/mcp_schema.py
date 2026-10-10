"""Print the input schema of neatlogs MCP tools.

    python scripts/mcp_schema.py create_detection preview_detection list_detections
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from mend.traces import MCP_URL


async def main(names: list[str]) -> None:
    headers = {"Authorization": f"Bearer {os.environ['NEATLOGS_API_KEY']}"}
    async with create_mcp_http_client(headers=headers) as http:
        async with streamable_http_client(MCP_URL, http_client=http) as (read, write, *_):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for tool in (await session.list_tools()).tools:
                    if not names or tool.name in names:
                        print(f"## {tool.name}\n{tool.description}\n{json.dumps(tool.input_schema, indent=1)}\n")


asyncio.run(main(sys.argv[1:]))
