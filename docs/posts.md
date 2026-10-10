# #neatHack post drafts

Every number below comes from a file in the repo. A human posts them; agents never post.
Tag @neatlogs, and @entirehq or @arithecfo where the post is about Entire or cfo.ai.

## 1. The bug it found in itself (screenshot: the demo trace, or the live video at 0:30)
our agent found its own bug. it read 200 of 233 lines of a file, then rewrote the whole file to change one word, silently deleting the rest. mend caught it in its @neatlogs traces and gave itself an edit tool. 27/28 -> 28/28 #neatHack
https://thegoodengineers.github.io/mend/?demo=1

## 2. Four rounds, no human
4 self-repair rounds, no human in the loop. each one: read traces, diagnose, patch itself, re-run all 29 tasks, keep only if it got better. tokens per suite run: 1,005,203 -> 432,858 #neatHack
https://github.com/thegoodengineers/mend#self-repair-rounds-all-four-kept

## 3. Held-out test (the "is it overfitting?" answer)
does self-repair just overfit? we ran 10 bugs it never saw. original worker: 9/10 twice. after self-repair: 10/10 twice, 60% fewer tokens #neatHack
https://github.com/thegoodengineers/mend#held-out-test-10-bugs-the-supervisor-never-saw

## 4. Live recording (attach video/live/mend-live.mp4)
same task, same model, recorded live at real speed. before: failed, 15 turns, 147k tokens. after mend fixed itself: passed, 4 turns, 18k tokens #neatHack

## 5. Regression guards (screenshot: neatlogs detections page, no keys visible)
every failure mend diagnoses becomes a @neatlogs detection, tested against real traces before it is created. so if a fixed bug ever comes back, neatlogs flags it #neatHack

## 6. Entire checkpoints (screenshot: the round 4 checkpoint page)
every fix mend makes to itself is written by claude code and linked to that session in @entirehq. and before each diagnosis, mend reads its own past checkpoints so it never retries a reverted fix #neatHack
https://entire.io/gh/thegoodengineers/mend/commit/7e2148e201fdaa9b2b3f921d1f2651950f537205

## 7. Every number is checked
every number in our README is recomputed from raw run files on every push. edit one by hand and CI goes red #neatHack
https://github.com/thegoodengineers/mend/actions

## 8. Submission (Monday 7:00-11:55 PM IST, quote the official neatlogs post)
Team The Good Engineers - Mend: an agent that fixes itself and proves it. repo: https://github.com/thegoodengineers/mend demo: https://thegoodengineers.github.io/mend/ #neatHack
