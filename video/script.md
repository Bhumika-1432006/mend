# Mend - demo video script (draft 1, written before the build)

Style: dark, calm, precise. Product palette (set once `report.html` has a theme). Ambient
CC BY music under the voice. Target 2:45, about 400 words. Numbers in brackets are filled in
only from measured runs; if a number doesn't exist, the line is cut.

| # | Scene | On screen | Narration |
|---|---|---|---|
| 1 | hook | Terminal: a worker agent's test run turns red. "FAILED" | Your agent just failed. Again. And nobody noticed. |
| 2 | problem | Three lines typing on: "silent failures", "hours in traces", "did the fix help?" | Agents fail quietly. Finding why takes hours of reading traces. And most fixes are never checked. |
| 3 | title | Logo, "Mend", one-line pitch | This is Mend. An agent that reads its own traces, fixes its own code, and proves it. |
| 4 | arch | Diagram: worker, neatlogs, supervisor, Entire, lighting up as named | A worker agent does the task. neatlogs traces every step. A supervisor reads those traces, patches the worker, and Entire records why. |
| 5 | demo-fail | CAPTURE: worker fails a task live | Here, the worker tries to fix a bug, and fails. |
| 6 | demo-trace | CAPTURE: neatlogs trace, failing span highlighted | The supervisor pulls the trace from neatlogs, and finds the exact step that went wrong. |
| 7 | demo-patch | CAPTURE: Entire checkpoint with the reasoning | It writes a fix to the worker itself. Entire saves the change, and the reasoning behind it. |
| 8 | demo-verify | CAPTURE: re-run, two traces side by side | Then it runs the same tasks again. If the score goes up, the fix stays. If not, it's reverted. |
| 9 | proof | Big number: [X] of 20 -> [Y] of 20 | Before Mend: [X] of twenty. After: [Y] of twenty. |
| 10 | recovery | CAPTURE: failed tool call and what the agent did next | And when an action fails mid-run, the trace shows exactly how it recovered. |
| 11 | business | cfo.ai model: pricing, costs, runway | We planned the business in cfo.ai: [pricing], [cost per run], and runway. |
| 12 | learn | Three lessons typing on | What we learned: [lesson one]. [lesson two]. [lesson three]. |
| 13 | close | Logo, repo URL, tagline | Mend. Agents that fix themselves, and prove it. |

## Shots only a human can record
- 10-15 s of the neatlogs dashboard showing our project's real traces (1920x1080, no cursor waving)
- 10-15 s of the Entire web view of a self-patch checkpoint
