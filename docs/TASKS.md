# Mend - tasks

Each task is self-contained: an agent or a teammate can pick it up cold. Tick it when the
"done" test passes. Owners: A lead/agents, B proof + posts, C report/demo + video, D floater (joins when free; picks any open task).
No task starts before the hackathon start time.

## Must
- [ ] **T01 (A) Repo + skeleton.** `mend/` package, `pyproject.toml`, `.gitignore` (incl. `.env`),
  `README.md` stub, `pytest` runs. Files: repo root. Done: `pytest` exits 0 on an empty test.
- [x] **T02 (A) neatlogs spike.** (10 Oct: `scripts/trace_check.py`; trace visible, but the Claude call itself failed on Anthropic credit - redo once credit exists.) Install the SDK per docs.neatlogs.com/sdk/python, init once at
  the entry point with a workflow name, one Claude call traced. Done: the trace is visible in
  the neatlogs dashboard (screenshot saved to `evidence/`).
- [ ] **T03 (B) Entire spike.** `entire enable` in the repo; make one change with Claude Code;
  commit. Done: an Entire checkpoint with the session is visible (`entire` CLI or web), output
  saved to `evidence/`.
- [x] **T04 (A) MCP read spike.** (10 Oct: `mend/traces.py`; `get_trace_context(created_after=...)` works, `search_traces` returned nothing for fresh traces.) From a script or Claude Code, call the neatlogs MCP
  `search_traces` and `get_trace_context` for the T02 trace. Done: the span tree prints.
- [ ] **T05 (B) Sandbox repo, first 5 bugs.** `sandbox/` small Python project with pytest; each bug
  is a `tasks/NN.json` (bug report text + a patch that introduces the bug). Done: for each task,
  applying the bug makes exactly its tests fail; reverting makes them pass (`pytest` script).
- [ ] **T06 (A) Worker agent.** `mend/worker.py`: Claude + tools `list_files`, `read_file`,
  `write_file`, `run_tests`; works in a temp copy of the sandbox with one bug applied.
  Done: solves at least 1 of the 5 tasks end to end; full run traced in neatlogs.
- [ ] **T07 (A) Suite runner.** `python -m mend.suite` runs all tasks, writes `runs/<id>.json`
  (task, pass/fail, trace id, duration, tokens if available). Done: a run file exists for a full suite.
- [ ] **T08 (B) 20 bugs.** Extend T05 to 20 tasks of mixed difficulty. Done: same check as T05, 20/20.
- [ ] **T09 (B) Baseline.** Run the suite 3 times on the unmodified worker. Done: the three pass
  counts are recorded in `hackathon.md` with run ids.
- [ ] **T10 (A) Supervisor: diagnose.** `mend/supervisor.py` takes a run file, pulls each failed
  task's trace over MCP, outputs a diagnosis (failing step, cause, proposed change) to
  `runs/<id>.diagnosis.md`. Done: a diagnosis that names a real span for at least one failure.
- [ ] **T11 (A) Supervisor: patch, re-run, keep or revert.** Apply the proposed change to the
  worker via headless Claude Code (`claude -p`), commit, re-run the suite, compare pass counts,
  `git revert` if not better. Done: one full round logged, with both run ids and the commit.
- [ ] **T12 (B, or D if free) cfo.ai business plan.** Pricing, costs (model + infra per run), revenue and
  runway scenarios for Mend. Done: plan exported to `docs/business-plan.*` and linked in README.
- [ ] **T13 (C) Report.** `python -m mend.report` turns `runs/*.json` into `report.html`:
  pass counts per round, per-task status, links to neatlogs traces and commits. Done: opens
  in a browser, no server.
- [ ] **T14 (B) Build in public.** One #neatHack post per milestone (spikes, first solve,
  baseline, first self-fix, video). Done: links listed in `hackathon.md`.
- [ ] **T15 (C) Video.** Playbook pipeline: `video/script.md` -> `narrate.py` -> scenes ->
  `record.py` -> `assemble.py`. Must cover neatlogs, Entire and cfo.ai (architecture,
  implementation, runtime, reasoning, result). Done: `final.mp4` is 3:00 or less, not sped up.
- [ ] **T16 (B) README evidence.** Every claim links to a trace, run file, checkpoint or post.
  Done: a teammate who didn't build it can follow each link.

## Should
- [ ] **T17 (A) Recovery.** Worker retries a failed tool call (e.g. test timeout) and the trace
  shows what it did next. Done: one traced run with a failed action and the recovery.
- [ ] **T18 (C) Demo mode.** `report.html?demo=1` steps through one round automatically for the
  video capture. Done: plays end to end unattended.
- [ ] **T19 (A) Multiple rounds.** Supervisor runs N rounds unattended, stops when no gain.

## Nice
- [ ] **T20** Two worker models compared on the same suite.
- [ ] **T21** Supervisor posts its own round summary as a draft (not auto-published).
