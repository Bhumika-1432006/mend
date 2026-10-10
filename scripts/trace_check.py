"""T02 spike: one Claude call, traced in neatlogs under a WORKFLOW span.

Run: python scripts/trace_check.py   (needs NEATLOGS_API_KEY and ANTHROPIC_API_KEY)
"""

import os
import uuid

import neatlogs

# init before importing anthropic, or calls get instrumented twice (neatlogs docs)
neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="mend-trace-check")

from anthropic import Anthropic  # noqa: E402

MODEL = os.environ.get("MEND_MODEL", "claude-opus-5-5")
RUN_ID = f"trace-check-{uuid.uuid4().hex[:8]}"
client = neatlogs.wrap(Anthropic(), run_id=RUN_ID)


@neatlogs.span(kind="WORKFLOW")
def trace_check(question: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": question}],
    )
    return next(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    try:
        print(RUN_ID)
        print(trace_check("In one sentence: why should an AI agent check its own work?"))
    finally:
        neatlogs.flush()
        neatlogs.shutdown()
