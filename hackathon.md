# neatHack build log

## Project
- Name: Mend (working title)
- Purpose (one sentence): an agent that reads its own neatlogs traces, rewrites its own code,
  and proves the fix with a re-run.
- Problem it addresses: agents fail quietly; diagnosing from traces and checking that a fix
  actually helped is slow and often skipped.
- Track: the only track, "Build an agent that works (literally)"

## Team
pending (only names/handles the builder chooses to publish)

## Stack
- Language / framework: pending (no code yet)
- LLM provider(s) / agent framework: pending
- neatlogs tracing: not set up yet; no code to instrument

## Build log

### 2026-10-08 - setup (before the event)
Done:
- Read https://neatlogs.com/hackathon/1 and https://luma.com/s5blr882 (summary under Submission).
- Installed the neathack skill at `.claude/skills/neathack/SKILL.md`. This is Claude Code's
  project-local skill folder, used instead of `.agents/skills/`. Its text matches the skill
  published on the event page.
- Created this log.

Checked:
- The project folder was empty before setup: no code, no manifest, no git repo.
- `NEATLOGS_API_KEY` is not set in the agent's shell. Only checked whether it exists; the
  value was never read.

Not done / blocked:
- neatlogs SDK not installed and nothing instrumented, because there is no language, entry
  point or LLM call yet. Next step once agent code exists.
- No sample trace sent: blocked on agent code and an API key.
- Not registered or submitted; that stays the builder's decision.

### 2026-10-08 - project-specific tracing prompt received
- The builder shared their neatlogs project's tracing prompt. Its key field is a placeholder,
  not a real key. It adds the regional ingest endpoint `https://ingest.neatlogs.com`.
- Still blocked: the folder has no agent code, and `NEATLOGS_API_KEY` is not set in the agent's
  shell. No SDK installed, no trace sent.
- Builder saved `NEATLOGS_API_KEY` as a Windows user environment variable. Checked that it
  exists and is 32 characters long; the value was never printed. The current agent shell can't
  see it until the app restarts. The key was shared in chat once, so replacing it with a new
  key is recommended.

### 2026-10-08 - planning: Stage 1 (how we get judged)
- Builder shared their own hackathon playbook, master prompt and video prompt. Ran Stage 1 of
  the master prompt: mapped the published rubric to what we must show. Planning only, no code.
- Pending from the builder: team, skills, GPU/resources, and a go for Stage 2 (choose the problem).

### 2026-10-09 - rules changed; problem shortlist (planning only)
- Re-read the event page (now https://neatlogs.com/hackathon) and Luma. The rules changed
  substantially: one track, three required tools (neatlogs, Entire, cfo.ai), new judging weights,
  submission by quote post on X. Old 4x25% rubric is superseded; see Submission.
- Updated `.claude/skills/neathack/SKILL.md` to the newly published official skill text (adds
  the three-tool requirement). The local copy had no edits of our own to preserve.
- Checked feasibility of an agent reading its own traces: the neatlogs MCP server documents
  `search_traces` and `get_trace_context` (https://docs.neatlogs.com/integrations/mcp). Not yet
  tried.
- Proposed problem shortlist to the builder. Decision pending. No code written.

### 2026-10-09 - team checked in
- Builder completed web check-in; the page shows all 4 team members checked in (which is the
  condition for AWS credits, first 200 teams). Whether we were within the first 200 is not shown.
- Wrote `neatHack_PS_and_Solution.pdf` (challenge summary and the proposed "Mend" plan).

### 2026-10-09 - tools installed (no project code)
- Entire CLI 0.11.4 installed natively on Windows with the official PowerShell installer;
  `entire version` reported `Entire CLI 0.11.4`, windows/amd64 (output pasted by the builder).
  The `curl | bash` installer, run from cmd, went into WSL instead; teammates should use
  `irm https://entire.io/install.ps1 | iex` in PowerShell.
- Already present on the lead's machine (checked by the agent): Git 2.54, Python 3.11.9,
  Node 22, GitHub CLI (logged in), Claude Code, ffmpeg, Playwright, edge-tts. An Anthropic API
  key exists as a user environment variable (only its presence was checked).
- Not done on purpose: Entire is not enabled in any repo yet, so no commits exist before kickoff.
- Builder reports: cfo.ai account created and joined the neatHack Discord (not verified by the agent).

### 2026-10-09 - plan written (planning only)
- Builder approved the Mend idea. Wrote `docs/PLAN.md` (pitch, rubric mapping, architecture,
  default stack, roles, timeline, risks), `docs/TASKS.md` (21 tasks with owners and done tests)
  and `video/script.md` (draft 1, numbers left blank until measured). No code.
- Builder reports they asked on Discord about the start time; answer not yet recorded here.
- Pending: permission to publish team names.
- Roles set: A lead/agents, B proof + posts + cfo.ai plan, C report + video, D floater (busy;
  joins when free).
- Wrote `docs/RUNBOOK.md` from the tools' docs: neatlogs SDK and MCP schemas, Entire setup
  (`commit_linking: always` for unattended commits), first-3-hours steps, design spec, sandbox
  plan, post plan, submission checklist. Open questions to try first: are headless `claude -p`
  sessions captured by Entire; can our Python client read traces over MCP.

### 2026-10-10 13:30 IST - event started; key verified
- Hackathon running (both the 12:00 AM and the 12:30 PM start have passed).
- Read the official neatlogs hackathon setup guide and the Entire hackathon guide; added the
  facts to `docs/RUNBOOK.md` (Entire checkpoint link + ID required; separate "Best Use of Entire"
  prize; AWS allowance is an EC2/Lambda-only sandbox, so not used).
- Created `.venv`; installed neatlogs 1.4.26, anthropic 1.13.0, mcp 2.3.0, pytest.
- Ran `python -m neatlogs doctor --probe` with the saved key: **Neatlogs Doctor: PASS**
  (TRACE_VISIBLE, TRACE_FINALIZED, HIERARCHY_VALID and 5 more PASS). The key works.
- Security note: a teammate-facing PDF made outside this project contained AWS sandbox login
  details; advised the builder to request a new password and keep it out of the repo.

## Demo
pending

## Known limitations and next steps
- All code must be written between kickoff (Oct 10, 12:30 PM IST) and the deadline. Planning
  ahead is allowed. Create the git repo and write the first code only after kickoff.
- Before building, confirm that the Entire CLI works on this Windows machine (the published
  install is a bash script) and that a cfo.ai account is usable.
- Once there is agent code: install the neatlogs SDK (https://docs.neatlogs.com/sdk), initialize
  it at the entry point, run one safe sample, and check that the trace shows up.
- Replace the neatlogs API key that was shared in chat.

## Submission
Confirmed from https://neatlogs.com/hackathon (read 2026-10-09; supersedes the 2026-10-08 summary):
- One track: "Build an agent that works (literally)". A single agent or a team of agents that
  completes a substantial task from start to finish. Focus areas: planning, tool use, state,
  context, execution, recovery, verification, iteration. Example tasks are ideas only.
- Required: neatlogs, Entire and cfo.ai, each with a clear role. neatlogs and Entire to build and
  improve the agent; cfo.ai to plan pricing, costs, revenue and runway. The business plan goes
  in the submission. The demo must cover all three tools.
- Pre-event work: you may plan in advance, but all code must be written between the start on
  Oct 10 and the deadline on Oct 12. Commits must show this.
- Teams of 1-4. Every member registers on Luma with the same team name; one team per person.
- Schedule (IST): intro call Oct 10 9:00 AM; kickoff Oct 10 12:30 PM; submissions Oct 12
  7:00-11:55 PM; winners Oct 16. Luma lists the event as Oct 10 12:00 AM - Oct 11 11:59 PM
  GMT+5:30, which differs. Confirm on Discord.
- Organiser email (Luma, from neatlogs, 9 Oct 2026 12:39 PM): hackathon begins Sat Oct 10,
  12:00 AM IST, when AWS and Crustdata credits are transferred; kickoff call 9:00 AM IST
  (workshops from Entire, AWS, neatlogs); Sunday workshops and office hours; closing call Mon
  Oct 12, 5:00-6:00 PM IST; submissions 7:00-11:55 PM IST on X, exact format to be sent;
  winners Oct 16. This agrees with Luma (12:00 AM start); the event page FAQ still says
  12:30 PM. Kept the email as evidence.
- How to submit: a public quote post on X of the official neatlogs submission post (team, name,
  project, public repo, demo link), using the Submit on X button shown in the window. Opening the
  draft does not submit. Demo video of 3 minutes or less. Public repo with evidence. Late
  submissions are not judged.
- Video must explicitly cover neatlogs, Entire and cfo.ai: architecture, implementation, runtime,
  reasoning and result for each.
- Judging: the agent 30%, use of neatlogs/Entire/cfo.ai 25%, demo video 20%, building in public
  15%, usefulness and originality 10%. Community winner judged separately on genuine interest;
  bought likes or bots disqualify.
- Evidence the page asks for: before/after runs (e.g. two neatlogs traces with the numbers
  compared); neatlogs trace links or screenshots; Entire checkpoints or entire-graph output; the
  cfo.ai business plan; a run where an action failed and what the agent did next; posts tagged
  #neatHack; a public repo with commits dated during the hackathon.
- Prizes: $2,000 / $1,000 / $500 cash plus $5,000 / $3,000 / $1,000 Dodo Payments credits;
  $500 community winner; 3 months neatlogs Pro per winner. AWS credits for the first 200 teams to
  complete web check-in; 5,000 Crustdata credits for everyone.
- Conduct: no harassment, spam or plagiarism.

Pending:
- The official submission post on X and the Submit on X button (appear in the submission window)
- Credit redemption details ("published with the resources")
- Web check-in for the team (builder to do)
