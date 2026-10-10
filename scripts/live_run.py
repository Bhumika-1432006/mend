"""Record a live worker run: every model call and tool call with real timestamps, to a JSONL file.

    python scripts/live_run.py 23 video/live/after.jsonl     (run from the repo whose worker you want)

The worker code is not changed: its client and tool handlers are wrapped from outside. The run is
traced in neatlogs as usual; the trace id is written into the first event.
"""

import json
import os
import sys
import time
from pathlib import Path

import neatlogs

neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="mend-live-recording")

from mend import worker  # noqa: E402
from mend.tasks import load_tasks, prepare, run_tests  # noqa: E402

task_id, out_path = sys.argv[1], Path(sys.argv[2])
out_path.parent.mkdir(parents=True, exist_ok=True)
log = out_path.open("w", encoding="utf-8")
t0 = time.time()


def emit(kind: str, **data) -> None:
    log.write(json.dumps({"t": round(time.time() - t0, 2), "kind": kind, **data}) + "\n")
    log.flush()


class LoggedMessages:
    def __init__(self, inner):
        self.inner = inner

    def create(self, **kwargs):
        emit("model_start", turn=sum(1 for m in kwargs["messages"] if m["role"] == "assistant") + 1)
        response = self.inner.create(**kwargs)
        text = next((b.text for b in response.content if b.type == "text"), "")
        emit("model_end", tokens_in=response.usage.input_tokens, tokens_out=response.usage.output_tokens,
             stop=response.stop_reason, text=text[:200])
        return response


class LoggedClient:
    def __init__(self, inner):
        self.messages = LoggedMessages(inner.messages)


worker._client = LoggedClient(worker.client())


def wrap(name, fn):
    def run(work, **args):
        shown = {k: (f"<{len(v)} chars>" if isinstance(v, str) and len(v) > 80 else v) for k, v in args.items()}
        emit("tool_start", tool=name, args=shown)
        try:
            out = fn(work, **args)
            emit("tool_end", tool=name, out=str(out).split("\n")[0][:120], ok=True)
            return out
        except Exception as exc:
            emit("tool_end", tool=name, out=("Error: " + str(exc)).replace(str(work), "<sandbox copy>")[:120], ok=False)
            raise
    return run


worker.HANDLERS = {name: wrap(name, fn) for name, fn in worker.HANDLERS.items()}

task = next(t for t in load_tasks() if t["id"] == task_id)
work = prepare(task)
emit("start", task=task_id, report=task["report"], model=worker.MODEL)
try:
    result = worker.solve_task(task["id"], task["report"], work)
    passed, _ = run_tests(work)
    emit("done", passed=passed, turns=result["turns"], trace_id=result["trace_id"],
         tokens=result["input_tokens"] + result["output_tokens"], stop=result["stop"])
    print(json.dumps({"passed": passed, "turns": result["turns"], "trace_id": result["trace_id"]}))
finally:
    log.close()
    neatlogs.flush()
    neatlogs.shutdown()
