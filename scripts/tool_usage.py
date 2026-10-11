"""Count the worker's tool calls per run, read back from neatlogs traces: why did tokens drop?

    python scripts/tool_usage.py <run_id> [<run_id> ...]   -> evidence/tool-usage.json (merged)
"""

import json
import sys
from collections import Counter
from pathlib import Path

from mend.suite import RUNS
from mend.traces import get_trace

OUT = Path(__file__).resolve().parent.parent / "evidence" / "tool-usage.json"


def count_run(run_id: str) -> dict:
    run = json.loads((RUNS / f"{run_id}.json").read_text(encoding="utf-8"))
    totals, missing = Counter(), 0
    for task in run["tasks"]:
        try:
            spans = get_trace(task["trace_id"]).get("spans") or []
        except Exception:
            missing += 1
            continue
        totals.update(s["name"] for s in spans if s.get("type") == "tool_call")
        totals["llm_calls"] += sum(1 for s in spans if s.get("type") == "llm")
    return {"run_id": run_id, "worker_commit": run["worker_commit"], "passed": run["passed"], "total": run["total"],
            "tokens": run["input_tokens"] + run["output_tokens"], "traces_missing": missing, "counts": dict(totals)}


if __name__ == "__main__":
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for rid in sys.argv[1:]:
        data[rid] = count_run(rid)
        print(rid, data[rid]["counts"], "missing", data[rid]["traces_missing"], flush=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
