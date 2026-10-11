"""Talk to a local neatroots (neatlogs' local trace checker) over its MCP endpoint.

    python scripts/neatroots.py tools                  # list its MCP tools
    python scripts/neatroots.py call <tool> '<json>'   # call one, print JSON

neatroots runs at http://localhost:4100 (installed in WSL; see hackathon.md).
"""

import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://localhost:4100/mcp"


async def run(argv: list[str]) -> None:
    async with streamable_http_client(URL) as (read, write, *_):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if argv[0] == "tools":
                for t in (await session.list_tools()).tools:
                    print(t.name, "-", (t.description or "")[:90])
                return
            result = await session.call_tool(argv[1], json.loads(argv[2]) if len(argv) > 2 else {})
            if result.structured_content:
                print(json.dumps(result.structured_content, indent=1)[:20000])
            else:
                print("\n".join(getattr(c, "text", "") for c in result.content)[:20000])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run(sys.argv[1:] or ["tools"]))
