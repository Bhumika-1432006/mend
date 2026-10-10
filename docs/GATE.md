# The gate (pre-registered)

These are the rules Mend uses to keep or revert a change to itself. They are written here and
committed before any further self-repair round runs, so every later round can be checked against
them. The code that enforces them is `one_round()` in [`mend/supervisor.py`](../mend/supervisor.py).

1. **Inputs.** A round starts from one suite run file (`runs/<id>.json`) of the 29 training tasks.
   The supervisor sees only the traces of that run's failed tasks and its 3 slowest passing tasks,
   plus the history of every earlier fix (kept, reverted or rejected).
2. **Never seen.** The 10 held-out tasks (`tasks/heldout.json`) and the 8 real-world tasks
   (`tasks/realworld.json`) are never shown to the supervisor; it refuses to run on those run files.
3. **What may change.** Only `mend/worker.py` and `mend/prompts/worker.md`. A patch that touches
   any other file, or whose added lines name a library module or a known bug, is rejected before
   anything runs (`*.rejected.round.json`).
4. **Keep rule.** After the patch, the same task list is re-run once. The patch is kept if
   - more tasks pass than before, or
   - the same number pass with at least 15% fewer tokens (input + output).
5. **Otherwise revert.** Anything else is reverted with `git revert`, and the diagnosis is kept.
6. **Every round is recorded,** kept or not, in `runs/<after-run>.round.json`, and appears in the
   README table; `python -m mend.verify` checks the README numbers against those files.
7. **Known limits.** One re-run per round (repeats are run separately and reported); token counts
   vary run to run by roughly ±10% in our repeats, which is why the token threshold is 15%.
