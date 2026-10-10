# Mend

An agent that reads its own [neatlogs](https://neatlogs.com) traces, rewrites its own code, and
proves the fix with a re-run. Built for neatHack (Oct 10-12, 2026) by team The Good Engineers.

Status: in progress. Nothing below is claimed until it is measured; see `hackathon.md` for the
dated build log and evidence.

- Plan: [docs/PLAN.md](docs/PLAN.md) - tasks: [docs/TASKS.md](docs/TASKS.md) -
  runbook: [docs/RUNBOOK.md](docs/RUNBOOK.md)

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # macOS/Linux: .venv/bin/pip
pytest
```

Needs `NEATLOGS_API_KEY` (neatlogs Project API key) and `ANTHROPIC_API_KEY` as environment
variables. Never commit them.
