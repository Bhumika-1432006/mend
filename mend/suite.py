"""Run the worker on the task suite and record the result.

    python -m mend.suite              # all 20 tasks
    python -m mend.suite 01 05 15     # selected tasks
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import neatlogs

from mend.tasks import ROOT, load_tasks, prepare

RUNS = ROOT / "runs"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def run_suite(task_ids: list[str] | None = None, label: str = "") -> dict:
    from mend import worker  # imported after neatlogs.init (see worker docstring)

    tasks = [t for t in load_tasks() if not task_ids or t["id"] in task_ids]
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S") + (f"-{label}" if label else "")
    run = {
        "run_id": run_id,
        "worker_commit": git("rev-parse", "--short", "HEAD"),
        "worker_dirty": bool(git("status", "--porcelain", "mend/worker.py", "mend/prompts")),
        "model": worker.MODEL,
        "tasks": [],
    }
    for task in tasks:
        work = prepare(task)
        try:
            result = worker.solve(task, work)
        except Exception as exc:  # an API failure on one task must not lose the whole run
            result = {"task_id": task["id"], "passed": False, "stop": "exception", "error": repr(exc)[:500]}
        finally:
            shutil.rmtree(work, ignore_errors=True)
        result["difficulty"] = task["difficulty"]
        run["tasks"].append(result)
        print(f"{task['id']} {'PASS' if result['passed'] else 'FAIL'}  turns={result.get('turns')}  stop={result.get('stop')}", flush=True)
    run["passed"] = sum(t["passed"] for t in run["tasks"])
    run["total"] = len(run["tasks"])
    run["input_tokens"] = sum(t.get("input_tokens", 0) for t in run["tasks"])
    run["output_tokens"] = sum(t.get("output_tokens", 0) for t in run["tasks"])
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{run_id}.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"run {run_id}: {run['passed']}/{run['total']} passed -> runs/{run_id}.json")
    return run


if __name__ == "__main__":
    neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="mend-worker")
    try:
        run_suite(sys.argv[1:] or None)
    finally:
        neatlogs.flush()
        neatlogs.shutdown()
