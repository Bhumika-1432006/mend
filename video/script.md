# Mend - demo video script (draft 2, 10 Oct evening; numbers from run files)

Target: 2:45 or less, about 400 words, never sped up. Must cover neatlogs, Entire and cfo.ai:
architecture, implementation, runtime, reasoning and result for each (submission rule).
Assets that already exist: `video/live/mend-live.mp4` (live recording, 1:55), the site
(https://thegoodengineers.github.io/mend/ incl. `?demo=1`), report.html, the README tables.
Every number below is checked by `python -m mend.verify` or comes from a run file.

| # | Scene | On screen | Narration |
|---|---|---|---|
| 1 | hook | Live recording: the original worker's `write_file` of the whole 7,526-char file, then the full suite FAILED | Our agent just broke working code to fix one line. Then it found out why, and fixed itself. |
| 2 | problem | Three lines typing on: "fails quietly", "hours in traces", "fixes never checked" | Agents fail quietly. Finding why takes hours of reading traces, and most fixes are never checked. |
| 3 | title | Mend wordmark (site hero) | This is Mend. An agent that fixes itself, and proves it. |
| 4 | arch (neatlogs + Entire) | Site "How it works" loop, steps lighting up | A worker agent does the job. neatlogs traces every model call and tool call. A supervisor reads those traces back over the neatlogs MCP server, diagnoses the failure, and has Claude Code patch the worker. Entire links each patch to the session that wrote it. |
| 5 | runtime (neatlogs) | Live recording, original worker failing (cut from mend-live.mp4) | Here is a live run. The worker reads only part of a file, rewrites all of it, and deletes working code. |
| 6 | reasoning (neatlogs) | runs/2026-10-10T09-15-17.diagnosis.md, the "read 200 of 233 lines" row | Mend's diagnosis, from the trace: the worker read two hundred of two hundred thirty-three lines, then rewrote the whole file. |
| 7 | implementation (Entire) | The round-4 or round-5 Entire checkpoint page: intent, files, transcript | The fix is written by Claude Code. Entire keeps the session behind every change, and Mend reads those checkpoints back as memory, so it never retries a reverted fix. |
| 8 | result | Live recording, repaired worker passing in 4 turns | Same task, same model. Four turns instead of fifteen. |
| 9 | gate | Site "Every self-repair round" table | Every fix must earn its place: a full re-run of twenty-nine tasks, kept only if it gets better. Five rounds, all kept. Tokens per run: from about a million to three hundred forty-eight thousand. |
| 10 | proof | Site "Held-out" and "Real-world" cards | Is it overfitting? On ten bugs it never saw: nine of ten before, ten of ten after, with sixty percent fewer tokens. [Real-world inflection result, if measured.] |
| 11 | guards (neatlogs) | neatlogs detections page: "Mend regression guards" | And every failure it diagnoses becomes a neatlogs detection, so if a fixed bug comes back, neatlogs flags it. |
| 12 | business (cfo.ai) | cfo.ai model + docs/business-plan.md measured table | We planned the business in cfo.ai. Self-repair cut our own cost per task from four cents to one and a half, which is what makes the pricing work. |
| 13 | close | Wordmark, repo + site URL | Mend. Agents that fix themselves, and prove it. |

## Shots only a human can record (1920x1080, no cursor waving, no keys visible)
- neatlogs dashboard: task 23 trace before (failed, 15 turns) and after; the "Mend regression guards" detections.
- Entire: the round 4 (7e2148e) or round 5 (c07f702) checkpoint page.
- cfo.ai: the Mend model (after the cost refresh).
