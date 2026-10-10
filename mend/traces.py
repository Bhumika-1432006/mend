"""Read traces back from neatlogs over its MCP server (https://ingest.neatlogs.com/mcp).

    python -m mend.traces <ISO timestamp>   # prints the latest trace created after it

Find a run's trace by time (`created_after`), not by text search: search is BM25 over indexed
span text and returned nothing for fresh traces when we tried it (10 Oct).
"""

import asyncio
import json
import os
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

MCP_URL = "https://ingest.neatlogs.com/mcp"


async def _call(tool: str, args: dict) -> dict:
    headers = {"Authorization": f"Bearer {os.environ['NEATLOGS_API_KEY']}"}
    async with create_mcp_http_client(headers=headers) as http:
        async with streamable_http_client(MCP_URL, http_client=http) as (read, write, *_):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, args)
    if result.is_error:
        raise RuntimeError(f"{tool} failed: {result.content}")
    if result.structured_content:
        return result.structured_content
    return json.loads(result.content[0].text)


def get_trace(trace_id: str | None = None, created_after: str | None = None, wait_s: int = 90) -> dict:
    """A trace by id, or the latest trace created after an ISO timestamp.

    A fresh trace answers "not found" for a while after the run (seen on 10 Oct), so retry.
    """
    args = {"trace_id": trace_id} if trace_id else {"created_after": created_after}
    deadline = time.time() + wait_s
    while True:
        try:
            return asyncio.run(_call("get_trace_context", args))
        except RuntimeError as exc:
            if "not_found" not in str(exc) or time.time() > deadline:
                raise
            time.sleep(10)


def span_lines(trace: dict) -> list[str]:
    """Indented span tree, one line per span, built from the flat `spans` list."""
    spans = trace.get("spans") or []
    children: dict[str, list] = {}
    for s in spans:
        children.setdefault(s.get("parent_span_id") or "", []).append(s)

    def walk(parent: str, depth: int) -> list[str]:
        out = []
        for s in children.get(parent, []):
            line = f"{'  ' * depth}{s.get('type')} {s.get('name')} [{s.get('status')}] {s.get('duration_ms', 0):.0f}ms"
            out.append(line)
            out += walk(s["span_id"], depth + 1)
        return out

    return walk("", 0)


if __name__ == "__main__":
    t = get_trace(created_after=sys.argv[1])
    print(f"{t['trace_id']}  {t.get('name')}  workflow={t.get('workflow')}  status={t.get('status')}  errors={t.get('error_count')}")
    print("\n".join(span_lines(t)))
