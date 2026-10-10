"""Print the tool calls of one task's neatlogs trace from a run file.

    python scripts/show_tools.py <run_id> <task_id>
"""

import json
import sys

from mend.suite import RUNS
from mend.traces import get_trace

run_id, task_id = sys.argv[1], sys.argv[2]
task = next(t for t in json.loads((RUNS / f"{run_id}.json").read_text(encoding="utf-8"))["tasks"] if t["task_id"] == task_id)
print(f"task {task_id}: passed={task['passed']} turns={task['turns']} trace={task['trace_id']}")
for span in get_trace(task["trace_id"])["spans"]:
    if span.get("type") != "tool_call":
        continue
    args = json.loads(span.get("input_value") or "{}")
    args.pop("work", None)
    out = str(span.get("output_value", "")).replace("\n", " ")[:110]
    print(f"{span['name']:<10} {span['status']:<8} {span.get('duration_ms', 0) / 1000:>5.1f}s  {json.dumps(args)[:90]}  => {out}")
