"""The worker agent: fixes one planted bug in a sandbox copy using four tools.

Manual tool-use loop (not the SDK's beta tool runner) so neatlogs' wrap() traces every
`messages.create` call and each tool call gets its own TOOL span.

The caller must run `neatlogs.init(...)` before calling `solve` (init must precede the
anthropic import, so the client is created lazily).
"""

import os
import time
from pathlib import Path

import neatlogs

from mend.tasks import run_tests

MODEL = os.environ.get("MEND_MODEL", "claude-opus-5-5")
MAX_TURNS = 15
PROMPT_FILE = Path(__file__).parent / "prompts" / "worker.md"

TOOLS = [
    {
        "name": "list_files",
        "description": "List all files in the project, relative to its root.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "read_file",
        "description": "Read a text file. Returns numbered lines starting at `start` (1-based), at most `lines` lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "start": {"type": "integer", "minimum": 1},
                "lines": {"type": "integer", "minimum": 1},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Replace the whole content of a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_tests",
        "description": "Run the pytest suite. Optional `pattern` is passed to pytest -k. Returns pass/fail and output.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "additionalProperties": False,
        },
    },
]

_client = None


def client():
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = neatlogs.wrap(Anthropic())
    return _client


def _safe_path(work: Path, rel: str) -> Path:
    """Resolve a tool-supplied path, refusing anything outside the sandbox copy."""
    path = (work / rel).resolve()
    if not path.is_relative_to(work.resolve()):
        raise ValueError(f"path outside the project: {rel}")
    return path


@neatlogs.span(kind="TOOL", tool_name="list_files")
def list_files(work: Path) -> str:
    return "\n".join(
        str(p.relative_to(work)).replace("\\", "/")
        for p in sorted(work.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    )


@neatlogs.span(kind="TOOL", tool_name="read_file")
def read_file(work: Path, path: str, start: int = 1, lines: int = 200) -> str:
    text = _safe_path(work, path).read_text(encoding="utf-8").splitlines()
    chunk = text[start - 1 : start - 1 + lines]
    return "\n".join(f"{start + i}: {line}" for i, line in enumerate(chunk))


@neatlogs.span(kind="TOOL", tool_name="write_file")
def write_file(work: Path, path: str, content: str) -> str:
    target = _safe_path(work, path)
    if "tests" in target.relative_to(work.resolve()).parts:
        raise ValueError("editing tests is not allowed")
    target.write_text(content, encoding="utf-8")
    return f"wrote {path} ({len(content)} chars)"


@neatlogs.span(kind="TOOL", tool_name="run_tests")
def run_tests_tool(work: Path, pattern: str = "") -> str:
    passed, output = run_tests(work, pattern)
    return f"{'PASSED' if passed else 'FAILED'}\n{output}"


HANDLERS = {"list_files": list_files, "read_file": read_file, "write_file": write_file, "run_tests": run_tests_tool}


def current_trace_id() -> str | None:
    """The active neatlogs trace id, read from the W3C traceparent the SDK can inject."""
    carrier: dict[str, str] = {}
    if neatlogs.inject_trace_context(carrier) and "traceparent" in carrier:
        return carrier["traceparent"].split("-")[1]
    return None


@neatlogs.span(kind="WORKFLOW")
def solve_task(task_id: str, report: str, work: Path) -> dict:
    """Run the agent loop on one task. Returns turns, tokens, stop reason and the trace id."""
    result = {"task_id": task_id, "trace_id": current_trace_id(), "turns": 0,
              "input_tokens": 0, "output_tokens": 0, "stop": None, "summary": ""}
    messages = [{"role": "user", "content": f"Bug report: {report}"}]
    system = PROMPT_FILE.read_text(encoding="utf-8")
    while result["turns"] < MAX_TURNS:
        result["turns"] += 1
        response = client().messages.create(
            model=MODEL, max_tokens=16000, system=system, tools=TOOLS, messages=messages,
            output_config={"effort": "medium"},
        )
        result["input_tokens"] += response.usage.input_tokens
        result["output_tokens"] += response.usage.output_tokens
        result["stop"] = response.stop_reason
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            result["summary"] = next((b.text for b in response.content if b.type == "text"), "")
            return result
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                content, is_error = HANDLERS[block.name](work, **block.input), False
            except Exception as exc:  # report tool failures back to the model, don't crash the run
                content, is_error = f"Error: {exc}", True
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
        messages.append({"role": "user", "content": tool_results})
    result["stop"] = "max_turns"
    return result


def solve(task: dict, work: Path) -> dict:
    """Solve one task in `work`, then judge it ourselves: pass = the full test suite passes."""
    started = time.time()
    result = solve_task(task["id"], task["report"], work)
    result["passed"], _ = run_tests(work)
    result["duration_s"] = round(time.time() - started, 1)
    return result
