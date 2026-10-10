"""Build report.html from runs/*.json: rounds, per-task results across runs, diagnoses.

    python -m mend.report    # writes report.html (static, no server)
"""

import html
import json

from mend.tasks import ROOT, load_tasks

RUNS = ROOT / "runs"
REPO = "https://github.com/thegoodengineers/mend"
OUT = ROOT / "report.html"


def esc(value) -> str:
    return html.escape(str(value))


def load_runs() -> list[dict]:
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RUNS.glob("*.json")) if "." not in p.stem]
    return [r for r in runs if r.get("tasks")]


def load_rounds() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RUNS.glob("*.round.json"))]


def commit_links(sha: str) -> str:
    return (f'<a href="{REPO}/commit/{esc(sha)}">{esc(sha)}</a> · '
            f'<a href="https://entire.io/gh/thegoodengineers/mend/commit/{esc(sha)}">Entire checkpoint</a>')


def render() -> str:
    runs, rounds = load_runs(), load_rounds()
    tasks = load_tasks()
    round_rows = "".join(
        f"<tr><td>{esc(r['before'])}</td><td>{r['before_passed']}/{r['total']}</td>"
        f"<td>{esc(r['after'])}</td><td>{r['after_passed']}/{r['total']}</td>"
        f"<td>{r.get('before_tokens', 0):,} → {r.get('after_tokens', 0):,}</td>"
        f"<td class=\"{'ok' if r['kept'] else 'bad'}\">{'kept' if r['kept'] else 'reverted'}</td>"
        f"<td>{commit_links(r['commit'])}</td></tr>"
        for r in rounds
    ) or '<tr><td colspan="7">No self-repair rounds yet.</td></tr>'

    head = "".join(f"<th title=\"{esc(r['run_id'])}\">{esc(r['run_id'][5:16])}<br><small>{esc(r['model'].replace('claude-', ''))}</small></th>" for r in runs)
    grid = []
    for t in tasks:
        cells = []
        for r in runs:
            res = next((x for x in r["tasks"] if x["task_id"] == t["id"]), None)
            if res is None:
                cells.append('<td class="na">-</td>')
                continue
            tip = f"turns {res.get('turns')}, stop {res.get('stop')}, trace {res.get('trace_id')}"
            cells.append(f"<td class=\"{'ok' if res['passed'] else 'bad'}\" title=\"{esc(tip)}\">"
                         f"{'pass' if res['passed'] else 'fail'}<small>{res.get('turns', '')}</small></td>")
        grid.append(f"<tr><th class=\"task\" title=\"{esc(t['report'])}\">{esc(t['id'])} <small>{esc(t['difficulty'])}</small></th>{''.join(cells)}</tr>")
    totals = "".join(f"<td><b>{r['passed']}/{r['total']}</b><br><small>{(r.get('input_tokens', 0) + r.get('output_tokens', 0)):,} tok</small></td>" for r in runs)

    diagnoses = "".join(
        f"<details><summary>Diagnosis of {esc(p.stem.replace('.diagnosis', ''))}</summary><pre>{esc(p.read_text(encoding='utf-8'))}</pre></details>"
        for p in sorted(RUNS.glob("*.diagnosis.md"))
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Mend report</title>
<style>
:root{{--bg:#0f1115;--card:#171a21;--ink:#e8eaee;--mute:#8a919e;--line:#262a33;--ok:#3ecf8e;--bad:#f16b6b}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:auto;padding:32px 16px}}
h1{{margin:0;font-size:28px}} p.sub{{color:var(--mute);margin:4px 0 24px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:20px;overflow-x:auto}}
h2{{font-size:16px;margin:0 0 12px}} table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;white-space:nowrap}}
td.ok{{color:var(--ok)}} td.bad{{color:var(--bad)}} td.na{{color:var(--mute)}}
small{{color:var(--mute);margin-left:4px}} a{{color:#8ab4ff}}
pre{{white-space:pre-wrap;color:var(--mute);font-size:13px}} summary{{cursor:pointer;margin:6px 0}}
</style></head><body><main>
<h1>Mend</h1>
<p class="sub">An agent that reads its own neatlogs traces, fixes its own code, and proves the fix with a re-run.
Every number below comes from a run file in <a href="{REPO}/tree/main/runs">runs/</a>.</p>
<section><h2>Self-repair rounds</h2><table><tr><th>Before</th><th>Passed</th><th>After</th><th>Passed</th><th>Tokens</th><th>Result</th><th>Patch</th></tr>{round_rows}</table></section>
<section><h2>Tasks across runs <small>(pass/fail and turns; hover for trace id)</small></h2><table><tr><th>Task</th>{head}</tr>{''.join(grid)}<tr><th>Total</th>{totals}</tr></table></section>
<section><h2>Diagnoses written by the supervisor</h2>{diagnoses or '<p>None yet.</p>'}</section>
</main></body></html>"""


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
