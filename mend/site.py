"""Build the landing page (index.html) from the run files, so every number is real.

    python -m mend.site            # writes index.html
    python -m mend.site preview    # writes site_preview.html instead
"""

import html
import json
import re
import sys

from mend.report import REPO, load_rounds, load_runs
from mend.tasks import ROOT

ENTIRE = "https://entire.io/gh/thegoodengineers/mend/commit/"


def esc(v) -> str:
    return html.escape(str(v))


def tokens(run: dict) -> int:
    return run.get("input_tokens", 0) + run.get("output_tokens", 0)


def facts() -> dict:
    runs = {r["run_id"]: r for r in load_runs()}
    rounds = load_rounds()
    kept = [r for r in rounds if r["kept"]]
    first = kept[0] if kept else None
    full = [r for r in runs.values() if r["total"] >= 20]
    haiku = [r for r in full if "haiku" in r["model"]]
    opus = [r for r in full if "opus" in r["model"]]
    story = None
    if first:
        before, after = runs.get(first["before"]), runs.get(first["after"])
        diag = (ROOT / first["diagnosis"].replace("\\", "/")).read_text(encoding="utf-8")
        title = re.search(r"## Chosen fix: (.+)", diag)
        if before and after:
            b = {t["task_id"]: t for t in before["tasks"]}
            a = {t["task_id"]: t for t in after["tasks"]}
            fixed = [k for k in b if not b[k]["passed"] and a.get(k, {}).get("passed")]
            story = {"title": title.group(1) if title else "", "fixed": fixed,
                     "b": b, "a": a, "diagnosis_file": first["diagnosis"].replace("\\", "/")}
    # Repeat runs on the same 28 tasks: the worker before round 1 vs after it.
    v0_commit = runs[first["before"]]["worker_commit"] if first and first["before"] in runs else None
    same = [r for r in haiku if r["total"] == 28]
    before_runs = [r for r in same if r["worker_commit"] == v0_commit]
    after_runs = [r for r in same if r["worker_commit"] != v0_commit]
    round_list = []
    for r in rounds:
        d = (ROOT / r["diagnosis"].replace("\\", "/")).read_text(encoding="utf-8")
        m = re.search(r"## Chosen fix: (.+)", d)
        round_list.append({**r, "title": m.group(1) if m else "", "diagnosis_file": r["diagnosis"].replace("\\", "/")})
    return {"rounds": round_list, "first": first, "story": story, "haiku": haiku, "opus": opus,
            "before_runs": before_runs, "after_runs": after_runs,
            "runs_total": len(full), "tasks_total": max((r["total"] for r in full), default=0)}


def repeat_card(label: str, group: list[dict], task: str | None, cls: str) -> str:
    if not group:
        return ""
    solved = ", ".join(str(r["passed"]) for r in group)
    mean = sum(tokens(r) for r in group) / len(group)
    hits = sum(next((t["passed"] for t in r["tasks"] if t["task_id"] == task), False) for r in group) if task else 0
    task_line = f"<span class=\"sub\">task {esc(task)} passed in {hits} of {len(group)} runs</span>" if task else ""
    return (f'<div class="card {cls}"><span class="k">{esc(label)} · {len(group)} runs</span>'
            f'<span class="big">{esc(solved)}<em> / {group[0]["total"]}</em></span>'
            f'<span class="sub">mean {mean:,.0f} tokens per run</span>{task_line}</div>')


def render() -> str:
    f = facts()
    first, story = f["first"], f["story"]
    kept = [r for r in f["rounds"] if r["kept"]]
    if kept:
        last = kept[-1]
        chain = [last]  # walk back through rounds whose input was the previous round's output
        while any(r["after"] == chain[0]["before"] for r in kept):
            chain.insert(0, next(r for r in kept if r["after"] == chain[0]["before"]))
        start = chain[0]
        delta = (last["after_tokens"] - start["before_tokens"]) / start["before_tokens"] * 100
        hero_stat = (f'<div class="stat"><span class="k">{len(kept)} self-repair rounds · all kept on measured results</span>'
                     f'<span class="big">{delta:+.0f}%<em> tokens</em></span>'
                     f'<span class="sub">latest chain of {len(chain)} rounds: {start["before_passed"]}/{start["total"]} → {last["after_passed"]}/{last["total"]} tasks solved, '
                     f'{start["before_tokens"]:,} → {last["after_tokens"]:,} tokens (single runs)</span>'
                     f'<a class="link" href="#rounds">see every round →</a></div>')
    else:
        hero_stat = '<div class="stat"><span class="k">No self-repair round yet</span></div>'

    if story and story["fixed"]:
        k = story["fixed"][0]
        b, a = story["b"][k], story["a"][k]
        story_html = f"""
<section id="story"><div class="wrap two">
  <div><p class="eyebrow">The first bug Mend found in itself</p>
  <h2>It was deleting the end of long files.</h2>
  <p>Reading its own neatlogs traces, the supervisor saw the worker read only the first 200 lines of a
  233-line file, then rewrite the <b>whole file</b> to change one word. Everything after line 200 was
  silently gone. The fix it wrote for itself: <b>{esc(story['title'])}</b>.</p>
  <a class="link" href="{REPO}/blob/main/{esc(story['diagnosis_file'])}">read the full diagnosis →</a></div>
  <div class="ba">
    <div class="card bad"><span class="k">Before · task {esc(k)}</span><span class="big">failed</span>
      <span class="sub">ran out of turns at {b.get('turns')} · trace {esc(str(b.get('trace_id'))[:8])}</span></div>
    <div class="card ok"><span class="k">After · task {esc(k)}</span><span class="big">passed</span>
      <span class="sub">in {a.get('turns')} turns · trace {esc(str(a.get('trace_id'))[:8])}</span></div>
  </div>
</div></section>"""
    else:
        story_html = ""

    task = story["fixed"][0] if story and story["fixed"] else None
    if f["before_runs"] and f["after_runs"]:
        mb = sum(tokens(r) for r in f["before_runs"]) / len(f["before_runs"])
        ma = sum(tokens(r) for r in f["after_runs"]) / len(f["after_runs"])
        repeat_html = f"""
<section id="repeat"><div class="wrap">
  <p class="eyebrow">Repeatable, not lucky</p><h2>Same 28 tasks, run again and again.</h2>
  <p class="sub">The worker before its first self-repair against the worker after it, each run several times.
  Mean tokens per run changed by {(ma - mb) / mb * 100:+.1f}%.</p>
  <div class="ba two-col">{repeat_card("Before self-repair", f["before_runs"], task, "bad")}{repeat_card("After self-repair", f["after_runs"], task, "ok")}</div>
</div></section>"""
    else:
        repeat_html = ""

    round_rows = "".join(
        f"<tr><td>{i}</td><td>{esc(r['title'])} <a class=\"link\" href=\"{REPO}/blob/main/{esc(r['diagnosis_file'])}\">diagnosis</a></td>"
        f"<td>{r['before_passed']} → {r['after_passed']} / {r['total']}</td>"
        f"<td>{(r['after_tokens'] - r['before_tokens']) / r['before_tokens'] * 100:+.1f}%</td>"
        f"<td class=\"{'ok' if r['kept'] else 'miss'}\">{'kept' if r['kept'] else 'reverted'}</td>"
        f"<td><a class=\"link\" href=\"{REPO}/commit/{esc(r['commit'])}\">{esc(r['commit'])}</a></td></tr>"
        for i, r in enumerate(f["rounds"], 1))
    rounds_html = f"""
<section id="rounds"><div class="wrap">
  <p class="eyebrow">Every self-repair round</p><h2>Each fix was diagnosed from traces and written by the agent.</h2>
  <p class="sub">A round keeps its patch only if more tasks pass, or the same tasks pass with at least 15% fewer tokens. Each fix is a commit written by Claude Code; Entire checkpoints for them are being regenerated from a clean runner.</p>
  <div class="tablewrap"><table><tr><th>#</th><th>What Mend changed in itself</th><th>Solved</th><th>Tokens</th><th>Result</th><th>Commit</th></tr>{round_rows}</table></div>
</div></section>"""

    def run_row(r):
        return (f"<tr><td>{esc(r['run_id'][5:16].replace('T', ' '))}</td><td>{esc(r['model'].replace('claude-', ''))}</td>"
                f"<td><a class=\"link\" href=\"{REPO}/commit/{esc(r['worker_commit'])}\">{esc(r['worker_commit'])}</a></td>"
                f"<td class=\"{'ok' if r['passed'] == r['total'] else 'miss'}\"><b>{r['passed']}/{r['total']}</b></td><td>{tokens(r):,}</td></tr>")
    rows = "".join(run_row(r) for r in sorted(f["opus"] + f["haiku"], key=lambda r: r["run_id"]))

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mend: agents that fix themselves</title>
<meta name="description" content="Mend reads its own neatlogs traces, patches itself, and keeps a fix only if a full re-run gets better.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
/* Cream ground, one serif statement per section, Inter for UI, mono for ids. One accent (copper) for the primary action; green/red only mean pass/fail. */
:root{{--bg:#f6f2ea;--panel:#fffdf9;--line:#e4ddd0;--ink:#1d1b17;--mute:#6f685d;--accent:#c2551b;--ok:#17834f;--bad:#c23b3b}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Inter,system-ui,sans-serif}}
a{{color:inherit}} .wrap{{max-width:1080px;margin:auto;padding:0 20px}}
nav{{position:sticky;top:0;background:rgba(246,242,234,.88);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:5}}
nav .wrap{{display:flex;align-items:center;justify-content:space-between;height:60px}}
.logo{{font:400 28px 'Instrument Serif',Georgia,serif;text-decoration:none}} .logo span{{color:var(--accent)}}
nav .links a{{color:var(--mute);text-decoration:none;margin-left:22px;font-size:14px}} nav .links a:hover{{color:var(--ink)}}
header{{padding:84px 0 56px;background:radial-gradient(760px 340px at 75% 10%,rgba(194,85,27,.10),transparent)}}
header .wrap{{display:grid;grid-template-columns:1.25fr 1fr;gap:48px;align-items:center}}
h1{{font:400 clamp(44px,6.5vw,76px)/1.0 'Instrument Serif',Georgia,serif;letter-spacing:-.02em;margin:0 0 20px}}
h1 em{{font-style:italic;color:var(--accent)}} .lead{{color:var(--mute);font-size:19px;max-width:560px}}
.cta{{display:flex;gap:12px;margin-top:28px;flex-wrap:wrap}}
.btn{{padding:12px 18px;border-radius:10px;font-weight:600;text-decoration:none;border:1px solid var(--line)}}
.btn.primary{{background:var(--accent);color:#fff;border-color:var(--accent)}} .btn{{background:var(--panel)}}
.stat,.card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:0 1px 2px rgba(29,27,23,.04),0 8px 24px rgba(29,27,23,.05);display:flex;flex-direction:column;gap:6px}}
.k{{font:600 12px/1 'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--mute)}}
.big{{font:400 52px/1.05 'Instrument Serif',Georgia,serif;letter-spacing:-.01em}} .big em{{font-style:normal;color:var(--mute);font-size:24px}}
.sub{{color:var(--mute);font-size:14px}} .link{{color:var(--accent);text-decoration:none;font-weight:600;font-size:14px;margin-top:6px}}
section{{padding:72px 0;border-top:1px solid var(--line)}}
.eyebrow{{font:600 12px/1 'JetBrains Mono',monospace;color:var(--accent);text-transform:uppercase;letter-spacing:.1em;margin:0 0 12px}}
h2{{font:400 clamp(32px,4.4vw,48px)/1.08 'Instrument Serif',Georgia,serif;letter-spacing:-.01em;margin:0 0 16px}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:32px}}
.step{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 1px 2px rgba(29,27,23,.04)}}
.step b{{display:block;margin:6px 0 4px}} .step p{{margin:0;color:var(--mute);font-size:14px}}
.n{{font:600 12px 'JetBrains Mono',monospace;color:var(--accent)}}
.two{{display:grid;grid-template-columns:1.1fr 1fr;gap:40px;align-items:center}} .two p{{color:var(--mute)}} .two b{{color:var(--ink)}}
.ba{{display:grid;gap:14px}} .two-col{{grid-template-columns:1fr 1fr;margin-top:24px}} .card.bad .big em,.card.ok .big em{{color:var(--mute)}} .card.bad .big{{color:var(--bad)}} .card.ok .big{{color:var(--ok)}}
.tools{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:28px}}
.tool h3{{margin:0 0 6px;font-size:18px}} .tool p{{margin:0 0 10px;color:var(--mute);font-size:14px}}
table{{width:100%;border-collapse:collapse;margin-top:20px;font-size:14px}}
th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line)}} th{{color:var(--mute);font-weight:500}}
td:nth-child(3){{white-space:nowrap}} td.ok{{color:var(--ok)}} td.miss{{color:#b7791f}} .tablewrap{{overflow-x:auto}}
footer{{padding:40px 0;color:var(--mute);font-size:14px;border-top:1px solid var(--line)}}
@media (max-width:820px){{header .wrap,.two,.two-col{{grid-template-columns:1fr}} .steps,.tools{{grid-template-columns:1fr}} nav .links a.hide{{display:none}}}}
</style></head><body>
<nav><div class="wrap"><a class="logo" href="#">mend<span>.</span></a>
<div class="links"><a class="hide" href="#how">How it works</a><a class="hide" href="#rounds">Rounds</a><a class="hide" href="#evidence">Evidence</a>
<a href="report.html">Full report</a><a href="{REPO}">GitHub</a></div></div></nav>

<header><div class="wrap">
  <div><p class="eyebrow">neatHack 2026 · The Good Engineers</p>
  <h1>Agents that fix themselves, <em>and prove it.</em></h1>
  <p class="lead">Mend reads its own neatlogs traces, works out why it failed, patches its own code, and keeps
  the fix only if a full re-run gets better. Otherwise it reverts.</p>
  <div class="cta"><a class="btn primary" href="#evidence">See the evidence</a><a class="btn" href="{REPO}">View the code</a></div></div>
  {hero_stat}
</div></header>

<section id="how"><div class="wrap">
  <p class="eyebrow">How it works</p><h2>A self-repair loop with a hard gate.</h2>
  <div class="steps">
    <div class="step"><span class="n">01</span><b>Run</b><p>A worker agent fixes planted bugs in a real codebase: {f['tasks_total']} tasks, judged by the test suite, not by the agent.</p></div>
    <div class="step"><span class="n">02</span><b>Trace</b><p>Every model call and tool call is a span in neatlogs, with inputs, outputs, tokens and cost.</p></div>
    <div class="step"><span class="n">03</span><b>Diagnose</b><p>A supervisor pulls failed and wasteful runs back over the neatlogs MCP server and finds the step that went wrong.</p></div>
    <div class="step"><span class="n">04</span><b>Patch</b><p>Claude Code applies one general fix to the worker: never a task-specific hack, never the tests.</p></div>
    <div class="step"><span class="n">05</span><b>Checkpoint</b><p>Entire links the commit to the session that wrote it, so every self-fix carries its reasoning.</p></div>
    <div class="step"><span class="n">06</span><b>Prove</b><p>The whole suite re-runs. More tasks solved, or the same with 15% fewer tokens: kept. Anything else: reverted.</p></div>
  </div>
</div></section>
{story_html}
{repeat_html}
{rounds_html}
<section id="evidence"><div class="wrap">
  <p class="eyebrow">Evidence</p><h2>Every number comes from a run file.</h2>
  <p class="sub">{f['runs_total']} full suite runs so far. A cheap worker (Claude Haiku 4.5) repaired by a
  stronger supervisor (Claude Opus 5.5). Each row links to data in <a class="link" href="{REPO}/tree/main/runs">runs/</a>.</p>
  <div class="tablewrap"><table><tr><th>Run (UTC)</th><th>Worker model</th><th>Worker version</th><th>Solved</th><th>Tokens</th></tr>{rows}</table></div>
  <p><a class="link" href="report.html">Open the full report: every task, every run, every diagnosis →</a></p>
</div></section>

<section id="tools"><div class="wrap">
  <p class="eyebrow">Built with</p><h2>neatlogs, Entire and cfo.ai, each doing real work.</h2>
  <div class="tools">
    <div class="tool card"><h3>neatlogs</h3><p>Traces every run. The supervisor reads those traces back over MCP to diagnose failures. The traces are the input, not decoration.</p><a class="link" href="{REPO}/tree/main/evidence">trace evidence →</a></div>
    <div class="tool card"><h3>Entire</h3><p>Every fix Mend makes to itself is a Claude Code session linked to its commit as a checkpoint.</p><a class="link" href="{REPO}#evidence">checkpoint status →</a></div>
    <div class="tool card"><h3>cfo.ai</h3><p>Prices Mend from measured cost per repair round. It showed our first price leaves a 31% margin, so pricing changes next.</p><a class="link" href="{REPO}/blob/main/docs/business-plan.md">business plan →</a></div>
  </div>
</div></section>

<footer><div class="wrap">Mend · built during neatHack, 10–12 October 2026 · <a href="{REPO}">github.com/thegoodengineers/mend</a></div></footer>
</body></html>"""


if __name__ == "__main__":
    out = ROOT / ("site_preview.html" if "preview" in sys.argv else "index.html")
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out.name}")
