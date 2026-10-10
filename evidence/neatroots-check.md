# Second opinion from neatroots (neatlogs' local trace checker), 10 Oct 2026 ~18:40 IST

neatroots 0.2.6 (github.com/neatlogs/neatroots, Apache-2.0) was installed in WSL and started on
localhost:4100. Both workers then ran tasks 22, 23, 24 and 29 with the neatlogs SDK pointed at it
(`NEATLOGS_ENDPOINT=http://localhost:4100`):

- original worker (13defdb files), project `mend-worker-original`: 2/4 passed (23 and 24 hit the turn limit)
- repaired worker (after 5 rounds), project `mend-worker-repaired`: 4/4 passed, 4-6 turns each

## neatroots' built-in checks
No problems flagged in either project. Its shipped rules look for loops, repeated identical calls,
error streaks and failed runs. The original worker's flaw (a valid, successful write_file that
deletes code) trips none of them, and the semantic questions need a local LLM we did not install.

## Tool calls in neatroots' own store (query_sql)
| Project | read_file | write_file (whole-file) | edit_file |
|---|---|---|---|
| mend-worker-original | 35 | 5 | 0 |
| mend-worker-repaired | 18 | 0 | 4 |

## Custom check: checks/neatroots/whole-file-rewrite.yaml
A `count` rule on write_file spans, previewed with neatroots' `preview_check` MCP tool over all 8
runs: **4 hits out of 8, and all 4 are the original worker's runs**; none of the repaired worker's.
Hit trace ids (neatroots-local): e5cf977f, 66c556d3, 0a15d169, b3cb3495.

Scripts: `scripts/neatroots.py` (MCP client for neatroots). The 8 side-experiment run files were
kept outside runs/ (MEND_RUNS_DIR) so they don't mix with the main evidence.
