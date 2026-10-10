# Mend - runbook

Prepared 9 Oct 2026 from the tools' public docs (planning, no code). "Verified" below means
"read in the docs", not "tried". Every item marked TRY is checked in the first spikes.

## 1. What the docs say (read 9 Oct)

### neatlogs Python SDK (docs.neatlogs.com/sdk/python, /integrations/anthropic)
- Install: `pip install -U "neatlogs[anthropic]" anthropic` (Python 3.10-3.13).
- `neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="...")` **before**
  importing `anthropic`, otherwise calls get instrumented twice.
- Capture Claude with `client = neatlogs.wrap(Anthropic())`. Use `wrap()` only; do not also list
  `instrumentations=["anthropic"]`.
- **Each `wrap()`ed call opens its own workflow root.** To keep one task = one trace, decorate the
  task function with `@neatlogs.span(kind="WORKFLOW")`, and our tools with
  `@neatlogs.span(kind="TOOL", tool_name="run_tests")`.
- Span kinds: WORKFLOW, AGENT, CHAIN, TOOL, RETRIEVER, EMBEDDING, GUARDRAIL, MCP_TOOL.
- Metadata: `neatlogs.wrap(Anthropic(), run_id=..., task_id=...)` shows as
  `neatlogs.workflow.<key>` attributes. We use this to find a task's trace later. TRY.
- End of a script: `neatlogs.flush()` then `neatlogs.shutdown()`, or spans are lost.
- Trace id: the docs only say "active span context". Plan: don't depend on it; find traces by
  `search_traces` on run/task id. TRY.
- Claude Code sessions can also be traced (docs.neatlogs.com/integrations/claude-code).
  Optional: makes the patch step visible in neatlogs too.

### neatlogs MCP (docs.neatlogs.com/integrations/mcp, /mcp-tools)
- Streamable HTTP at `https://ingest.neatlogs.com/mcp`, header `Authorization: Bearer <project key>`.
- `search_traces {query (required), limit=50 (max 100), offset, filters{status, framework,
  min/max_latency_ms, min/max_cost, date_range}}` -> `traces[{trace_id, name, status,
  created_at, latency_ms, error_message, cost, framework, agent_name, url}]`.
- `get_trace_context {trace_id}` -> `root_span` with nested `children`; each span has span_id,
  span_type, name, status, latency_ms, start_time, input, output, error, metadata (max 1000 spans).
- Also `triage_*` tools (neatlogs' own fix suggestions). We may read them as a second opinion.
- From Python: the official `mcp` package's streamable-HTTP client. TRY in T04.

### Entire (docs.entire.io)
- `entire login`, then in the repo: `entire enable -y --agent claude-code`
  (adds hooks to `.claude/settings.json`; `entire agent add claude-code` is the same idea).
- Checkpoint = git hook links a commit to the agent session (prompt, transcript, tool calls,
  files, tokens). Commits made by the agent itself are linked too.
- **Make linking non-interactive** (needed for the supervisor): `.entire/settings.json`
  `{ "commit_linking": "always" }`.
- Inspect: `entire checkpoint list`. Stored in the repo on its own git ref / checkpoints branch.
- **Unknown: whether headless `claude -p` sessions are captured.** TRY first (T03). Fallback:
  the supervisor writes its diagnosis to a file and commits it with the patch.
- entire-graph: `entire plugin install graph`, `entire graph init-agents --repo .`; needs Git
  2.36+ (we have 2.54); creates `.entire/graph-agent.md`, `AGENTS.md`, `CLAUDE.md`. Evidence:
  those files plus `entire graph version`. Language support not stated. TRY.

### cfo.ai
- "Ari" builds a financial model from questions; also reachable "from your own terminal over
  MCP" (not needed). We only need the business plan: pricing, costs, revenue, runway.

### Added 10 Oct (official pages, read 1:30 PM IST)
- neatlogs hackathon guide (neatlogs.com/hackathon/neatlogs-setup-guide.html): use the
  **Project API key**, not the `nlw_` HTTP key (that gives 401). Check with
  `python -m neatlogs doctor --probe` (want TRACE_VISIBLE and TRACE_FINALIZED = PASS).
  Reading traces from a terminal: `npm i -g neatlogs-cli@0.2.0`, `neatlogs auth login --device`,
  `neatlogs traces list/get --json` - a fallback if MCP reads fail.
- Entire hackathon guide (hack.entire.io/neathacks-2026): everyone signs in to entire.io with
  GitHub; the repo owner/org admin installs the Entire GitHub App and imports the repo. Submit an
  accessible checkpoint link `https://entire.io/gh/OWNER/REPO/commit/FULL_SHA` plus the checkpoint
  ID; `entire status` checks sync. Separate prize: "Best Use of Entire" (Checkpoints, Graph or
  Brain). Their idea list includes "a debugger for agent mistakes".
- AWS allowance is a sandbox IAM login: us-east-1 only; EC2, Lambda, IAM roles, load balancers
  only (no Bedrock). Not needed for Mend. Credentials must never enter the repo.

## 2. First 3 hours (exact steps, after the start time)

Lead (A):
1. `gh repo create <org>/mend --public --clone`; copy `docs/`, `video/`, `hackathon.md`,
   `.claude/skills/` in; first commit "docs: plan written before the event" (say so honestly).
2. Python venv; `pip install -U "neatlogs[anthropic]" anthropic pytest mcp`.
3. T02: a 10-line script: init -> wrap -> one Claude call inside a WORKFLOW span -> flush.
   Check the dashboard. Screenshot to `evidence/`.
4. T04: Python MCP client: `search_traces` for that run, then `get_trace_context`. Print span names.

Proof (B), in parallel:
1. Clone. `entire login`; `entire enable -y --agent claude-code`; add
   `.entire/settings.json` with `commit_linking: always`; commit it.
2. T03a: interactive Claude Code edits a file and commits -> `entire checkpoint list` shows it.
3. T03b: the same with `claude -p "..."` (headless). Record whether a checkpoint appears.
   This decides the patch-step design. Tell A immediately.
4. Start T05 (sandbox).

Report (C): start T13 against a hand-written sample `runs/sample.json` in the format below.

Decision at hour 3: if T03b fails, switch the patch step to "supervisor writes the patch itself
+ commits diagnosis file". If T04 fails, ask neatlogs on Discord (their team runs office hours);
meanwhile the supervisor reads a local copy of each run's tool calls, and neatlogs is still shown
in its own dashboard.

## 3. Design spec

### Worker (`mend/worker.py`)
- Input: task (bug report text), path to a temp copy of `sandbox/` with the bug applied.
- Tools (each a TOOL span): `list_files()`, `read_file(path, start=1, lines=200)`,
  `write_file(path, content)`, `run_tests(pattern="")` (pytest, 60 s timeout).
- Loop: Claude tool-use loop, max N turns; ends when the model stops calling tools.
- Result: pass = full `pytest` passes in the temp copy after the loop (checked by the runner,
  not by the worker's own claim).
- v0 is deliberately plain: one system prompt, no planning step, no retry policy. We say this
  openly; v0 is our honest baseline, not a sabotaged one.

### Run file (`runs/<run_id>.json`)
```json
{"run_id": "2026-10-10T14-05-r0", "worker_commit": "abc123", "model": "...",
 "tasks": [{"task_id": "07", "passed": false, "turns": 12, "duration_s": 41.2,
            "error": "max turns", "trace_query": "run_id=... task_id=07", "trace_url": "..."}],
 "passed": 9, "total": 20}
```

### Supervisor (`mend/supervisor.py`)
1. Read the latest run file; for each failed task fetch its trace (MCP).
2. Ask Claude for a diagnosis per failure: failing span, cause, and whether the fix is a
   *general* worker improvement (prompt, tool, loop policy) - never a task-specific hack.
3. Cluster failures; pick the single most common cause; write `runs/<run_id>.diagnosis.md`.
4. Patch: `claude -p` in the repo with the diagnosis, limited to `mend/worker.py` and
   `mend/prompts/`; commit "fix(worker): ..." (Entire links the session).
5. Re-run the suite -> new run file. Keep if passed count rose; else `git revert` and record it.
6. Guardrails: never edit `sandbox/`, `tasks/` or tests; refuse task-specific string matches.

### Report (`mend/report.py` -> `report.html`)
Rounds table (run id, worker commit, passed/total), per-task grid (pass/fail per round),
links to traces and commits, diagnosis text. Static file, one inline stylesheet.

## 4. Sandbox and tasks (plan for B)
A small invoicing library, `sandbox/invoicer/`: `money.py` (Decimal amounts, rounding),
`dates.py` (due dates, business days), `tax.py`, `discounts.py`, `csv_import.py`, `report.py`,
with a pytest suite. Each task = `tasks/NN.json` `{id, title, report, bug_patch}`.

Mix of 20 (8 easy, 8 medium, 4 hard), for example:
- easy: off-by-one in business days; `<` vs `<=` in a discount threshold; wrong rounding mode;
  wrong dict key in CSV mapping; missing strip() on CSV values
- medium: float instead of Decimal; mutable default argument; empty input crashes; timezone-naive
  date compare; exception swallowed and wrong value returned
- hard: bug spans two modules; misleading bug report (the test tells the truth); fix needs a
  file longer than one `read_file` page; test that takes > 60 s unless the fix is right

The hard ones are where a plain v0 worker tends to fail for *general* reasons (doesn't read the
failing test, gives up on long files, misreads timeouts). That is what the supervisor can
legitimately learn to fix. Check: each bug makes exactly its own tests fail.

## 5. Building in public (B posts, #neatHack, tag @neatlogs)
1. Start: "48 hours to build an agent that fixes itself. Plan: worker + supervisor + neatlogs
   traces + Entire checkpoints. #neatHack"
2. First trace: screenshot of the first neatlogs trace.
3. Baseline: "v0 worker solves X of 20. Here is the trace of one failure." (real numbers only)
4. First self-fix: the diagnosis, the Entire checkpoint, the new score.
5. Video: the final cut, then the submission quote post.

## 6. cfo.ai session (B, or D if free; Sunday)
Answer for Ari: who pays (teams running agents in production), pricing idea (per verified fix
or per seat), cost per suite run (measured: tokens x price from our runs), infra cost, scenarios
(base/growth), runway. Export the plan to `docs/business-plan.*`.

## 7. Submission checklist (Mon 12 Oct, window 7:00-11:55 PM IST)
- [ ] Video 3:00 or less, covers neatlogs, Entire and cfo.ai (architecture, implementation,
      runtime, reasoning, result)
- [ ] Public repo; commits dated during the event; README with evidence links
- [ ] Evidence: before/after traces with numbers, a failed action + recovery, Entire checkpoints,
      business plan, #neatHack post links
- [ ] Quote post of the official neatlogs post via "Submit on X", with team, name, project,
      repo, demo link - published, not just drafted (the builder does this, not the agent)
- [ ] Links checked in an incognito window
