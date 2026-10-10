# Mend

**An agent that reads its own [neatlogs](https://neatlogs.com) traces, fixes its own code, and
keeps the fix only if a full re-run gets better.** Built during
[neatHack](https://neatlogs.com/hackathon), 10–12 October 2026, by team The Good Engineers.

**Website:** https://thegoodengineers.github.io/mend/ · **Full data report:**
[report.html](https://thegoodengineers.github.io/mend/report.html) · **Build log:**
[hackathon.md](hackathon.md)

Every number in this README comes from a file in [`runs/`](runs/) or [`evidence/`](evidence/).
If a number has no file behind it, it is not here.

## How it works

```
worker agent ──runs 29 tasks──▶ neatlogs traces every model call and tool call
      ▲                                   │
      │                                   ▼  (neatlogs MCP: get_trace_context)
 keep or revert ◀── re-run the suite ◀── supervisor diagnoses failed + wasteful runs
                                          │
                                          ▼
                     Claude Code applies ONE general fix to the worker,
                     committed and captured as an Entire checkpoint
```

1. **Run.** A worker agent ([`mend/worker.py`](mend/worker.py), Claude Haiku 4.5) fixes planted
   bugs in a small invoicing library ([`sandbox/`](sandbox/), 37 tests). There are 29 tasks in
   [`tasks/tasks.json`](tasks/tasks.json). Pass means the library's test suite passes, judged
   by the runner, not by the agent.
2. **Trace.** Every model call and tool call is a span in neatlogs (one WORKFLOW span per task,
   TOOL spans per tool call). Each run file stores the task's neatlogs trace ID.
3. **Diagnose.** The supervisor ([`mend/supervisor.py`](mend/supervisor.py), Claude Opus 5.5)
   pulls the traces of failed tasks and the slowest passing tasks back over the neatlogs MCP
   server ([`mend/traces.py`](mend/traces.py)). It writes a diagnosis naming the failing step
   and one general fix.
4. **Patch.** Headless Claude Code applies the fix to `mend/worker.py` or
   `mend/prompts/worker.md` only. A guard rejects patches that touch other files or name
   specific library code.
5. **Prove.** The suite re-runs. The patch is kept if more tasks pass, or the same tasks pass
   with at least 15% fewer tokens. Otherwise it is reverted with `git revert`.

## Results

### Self-repair rounds (all four kept)

| # | What Mend changed in itself | Solved | Tokens | Commit | Diagnosis |
|---|---|---|---|---|---|
| 1 | Added an exact-replace `edit_file` tool; steered edits away from whole-file rewrites | 27 → 28 / 28 | 933,181 → 851,463 (−8.8%) | `e8a6baf` | [diagnosis](runs/2026-10-10T09-15-17.diagnosis.md) |
| 2 | `edit_file` shows the current text of a near match on a miss; clearer line prefixes | 28 → 29 / 29 | 1,005,203 → 894,839 (−11.0%) | `f9dae91` | [diagnosis](runs/2026-10-10T10-17-27.diagnosis.md) |
| 3 | Test-first workflow; stop as soon as the suite passes | 29 → 29 / 29 | 894,839 → 618,906 (−30.8%) | `931ea51` | [diagnosis](runs/2026-10-10T10-30-26-after.diagnosis.md) |
| 4 | Loop hands the worker the file list up front and finishes automatically once the full suite passes after an edit | 29 → 29 / 29 | 618,906 → 432,858 (−30.1%) | [`7e2148e`](https://entire.io/gh/thegoodengineers/mend/commit/7e2148e201fdaa9b2b3f921d1f2651950f537205) (Entire checkpoint) | [diagnosis](runs/2026-10-10T10-41-18-after.diagnosis.md) |

Round records: the `*.round.json` files in [`runs/`](runs/). Rounds 2 and 3 were run back to back with
`python -m mend.supervisor <run> --rounds 2`; round 4 ran from a clean runner clone. Rounds 2-3 "after" figures are single runs. The worker after round 4 was run three times: 29/29 each time ([10-59-46](runs/2026-10-10T10-59-46-after.json) 432,858, [11-13-11](runs/2026-10-10T11-13-11.json) 451,105, [11-18-45](runs/2026-10-10T11-18-45.json) 456,563 tokens). **Caveat:** the supervisor learns from the same 29 tasks it is scored on, and round 3's prompt includes a rule for hanging test suites learned from task 29; on a held-out set it never sees, it also improved (below).

**The first bug Mend found in itself.** The worker read only the first 200 lines of the
233-line `ledger.py`, then rewrote the whole file to change one word. That silently deleted
everything after line 200. Task 23 failed at the 15-turn limit; after the fix it passed in 8
turns.

### Repeatable, not lucky: same 28 tasks, 3 runs each

| Worker | Runs | Solved | Mean tokens per run | Task 23 |
|---|---|---|---|---|
| Before self-repair (`13defdb`) | [09-15-17](runs/2026-10-10T09-15-17.json), [10-17-27-v0](runs/2026-10-10T10-17-27-v0.json), [10-28-58-v0](runs/2026-10-10T10-28-58-v0.json) | 27, 26, 27 | 946,860 | passed 0 of 3 |
| After round 1 | [09-31-07](runs/2026-10-10T09-31-07-after.json), [09-40-55](runs/2026-10-10T09-40-55.json), [09-51-17](runs/2026-10-10T09-51-17.json) | 28, 28, 28 | 875,953 (−7.5%) | passed 3 of 3 |

### Held-out test: 10 bugs the supervisor never saw

[`tasks/heldout.json`](tasks/heldout.json) holds 10 more planted bugs. They are never shown to the
supervisor (it refuses held-out runs) and no diagnosis or patch is based on them.

| Worker | Runs | Solved | Mean tokens per run | Turns |
|---|---|---|---|---|
| Original (`13defdb`) | [11-25-59](runs/2026-10-10T11-25-59-heldout-v0.json), [11-32-56](runs/2026-10-10T11-32-56-heldout-v0.json) | 9, 9 of 10 | 388,977 | 83, 86 |
| After 4 self-repair rounds | [11-30-57](runs/2026-10-10T11-30-57-heldout.json), [11-37-44](runs/2026-10-10T11-37-44-heldout.json) | 10, 10 of 10 | 156,587 (−59.7%) | 46, 48 |

The original worker's held-out runs used `mend/worker.py` and `mend/prompts/worker.md` from
`13defdb` on the current harness (noted in each run file as `worker_version`).

### Live recording

[`video/live/mend-live.mp4`](video/live/mend-live.mp4) (1:55, also on the website): the original and
the repaired worker run task 23 live, replayed at real speed from event logs written during the
runs ([`scripts/live_run.py`](scripts/live_run.py), [`video/live/make_video.py`](video/live/make_video.py)).
Original: failed, 15 turns, 147,457 tokens (trace `1ef860cd`). Repaired: passed, 4 turns, 17,847
tokens (trace `9b29c189`). Narration is synthetic voice.

For reference, the same worker on Claude Opus 5.5 solved the first 20 tasks: 20/20, 162,006
tokens ([run](runs/2026-10-10T08-37-19.json)).

## Evidence

| Claim | Evidence |
|---|---|
| Runs are traced in neatlogs and read back by the agent | [`evidence/t02-first-traced-call.txt`](evidence/t02-first-traced-call.txt), [`evidence/t04-trace-readback.txt`](evidence/t04-trace-readback.txt); each run file has per-task `trace_id`s |
| The agent recovers from a failed action | [`evidence/t17-recovery-from-timeout.txt`](evidence/t17-recovery-from-timeout.txt): `run_tests` timed out after 60 s, then the worker found and fixed the infinite loop (task 29) |
| Before/after with the numbers compared | the tables above; every row links to its run file |
| Self-fixes are written by Claude Code and committed by the supervisor | commits `e8a6baf`, `f9dae91`, `931ea51` (`fix(worker): …`) |
| Entire checkpoints | round 4: [checkpoint `01M4JQG23JYXJ34SHA46MCGMV2`](https://entire.io/gh/thegoodengineers/mend/commit/7e2148e201fdaa9b2b3f921d1f2651950f537205) on commit `7e2148e`, the supervisor's own Claude Code session; see note below |
| Business plan with cfo.ai | [`docs/business-plan.md`](docs/business-plan.md), export [`docs/business-plan-cfo-ai.xlsx`](docs/business-plan-cfo-ai.xlsx) |
| Code written during the hackathon | commit history; the first commit holds only plans written before the event, as the rules allow |
| Building in public | [first #neatHack post](https://x.com/theintrodev/status/2108851736765141188) |

**Note on Entire checkpoints.** Entire captured the supervisor's headless Claude Code sessions
as checkpoints, for example the session behind `e8a6baf`. Those checkpoints also included the
lead's own interactive chat, so we removed them from the public repo. New checkpoints are
created from a separate clean clone that only runs the supervisor (round 4 onwards).

## Built with

- **neatlogs:** tracing (Python SDK, `wrap()` + `@neatlogs.span`) and reading traces back over
  the neatlogs MCP server. The traces are the supervisor's input.
- **Entire:** Claude Code hooks plus `commit_linking: always` link each self-fix commit to the
  Claude Code session that wrote it. Publicly available today: round 4's checkpoint (the earlier
  ones were removed because they also contained the lead's own chat; their commits still carry
  `Entire-Checkpoint` trailers that now point nowhere).
- **cfo.ai:** pricing, costs, revenue and runway, from our measured cost per repair round.
- **Claude:** Haiku 4.5 as the worker, Opus 5.5 as the supervisor, Claude Code for patches.

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # macOS/Linux: .venv/bin/pip
pytest                                  # unit tests + checks that all 29 planted bugs break the sandbox
```

Needs `NEATLOGS_API_KEY` (neatlogs Project API key) and `ANTHROPIC_API_KEY` as environment
variables. Never commit them.

```bash
python -m mend.suite                 # run the worker on all tasks -> runs/<run_id>.json
python -m mend.supervisor --rounds 2 # self-repair rounds on the latest run
python -m mend.site                  # rebuild index.html from the run files
python -m mend.report                # rebuild report.html
```

The supervisor needs the Claude Code CLI (`claude`) for the patch step, and a clean git tree.
