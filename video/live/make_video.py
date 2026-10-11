"""Make video/live/mend-live.mp4: two live worker runs replayed at real speed, with narration.

    python video/live/make_video.py        (system Python with playwright + edge-tts; ffmpeg on PATH)

Inputs are the event logs written by scripts/live_run.py while the worker actually ran:
before.jsonl (original worker, commit 13defdb) and after.jsonl (current worker), plus the round-1
diagnosis. Tool calls appear at the second they happened. Nothing is sped up.
"""

import asyncio
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
VOICE = "en-US-AndrewNeural"
INTRO, DIAG, RESULT, TAIL = 9.0, 12.0, 11.0, 2.0


def events(name: str) -> list[dict]:
    return [json.loads(line) for line in (HERE / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]


def replay(evts: list[dict]) -> tuple[list[dict], float, dict]:
    start = next(e for e in evts if e["kind"] == "start")["t"]
    done = next(e for e in evts if e["kind"] == "done")
    lines = []
    for e in evts:
        at = round(e["t"] - start, 2)
        if e["kind"] == "model_start":
            lines.append({"at": at, "cls": "think", "text": f"turn {e['turn']} · model thinking…"})
        elif e["kind"] == "tool_start":
            args = ", ".join(f"{k}={v}" for k, v in e["args"].items())
            lines.append({"at": at, "cls": "call", "text": f"→ {e['tool']}({args})"})
        elif e["kind"] == "tool_end":
            cls = "res bad" if (not e["ok"] or e["out"].startswith("FAILED") or e["tool"] == "write_file") else "res"
            if e["tool"] in ("edit_file",) or e["out"].startswith("PASSED"):
                cls = "res ok"
            out = re.sub(r"[A-Za-z]:\\?[^'\"]*?mend-\d+-[a-z0-9_]+", "<sandbox copy>", e["out"])
            lines.append({"at": at, "cls": cls, "text": "   " + out})
    return lines, round(done["t"] - start, 2) + TAIL, done


def build() -> tuple[dict, list[dict]]:
    before, after = events("before"), events("after")
    b_lines, b_dur, b_done = replay(before)
    a_lines, a_dur, a_done = replay(after)
    report = before[0]["report"]
    write_at = next(l["at"] for l in b_lines if "write_file" in l["text"])
    fail_at = next(l["at"] for l in b_lines if l["text"].strip().startswith("FAILED") and l["at"] > write_at)
    t_b, t_d = INTRO, INTRO + b_dur
    t_a = t_d + DIAG
    t_r = t_a + a_dur
    total = t_r + RESULT
    data = {"report": report, "before": {"lines": b_lines, "start": t_b, "dur": b_dur, "done": b_done},
            "after": {"lines": a_lines, "start": t_a, "dur": a_dur, "done": a_done},
            "diag_at": t_d, "result_at": t_r, "total": total}
    narration = [
        {"at": 0.5, "text": f"This is a live recording of Mend, at real speed. A customer reports: {report}"},
        {"at": t_b + 0.5, "text": "First, the original worker."},
        {"at": t_b + write_at + 0.3, "text": "It rewrites the whole file to change one line, but it had only read part of it."},
        {"at": t_b + fail_at + 1.0, "text": "The full test suite now fails. The rewrite deleted working code, and the worker spends its remaining turns chasing the damage."},
        {"at": t_d + 0.5, "text": "Mend's supervisor reads this run back from neatlogs, finds the step that went wrong, and patches its own worker with Claude Code. "
                                  "The patch is kept only because a full re-run got better."},
        {"at": t_a + 0.3, "text": "Same task, same model, the repaired worker."},
        {"at": t_r + 0.5, "text": f"{a_done['turns']} turns instead of {b_done['turns']}. {a_done['tokens']:,} tokens instead of {b_done['tokens']:,}. Fixed, and proven."},
    ]
    return data, narration


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@800&family=Instrument+Serif:ital@1&family=Inter:wght@500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#e6e6dd;color:#0f0f0d;font-family:Inter,sans-serif}
.scene{position:absolute;inset:0;padding:90px 120px;box-sizing:border-box;opacity:0;transition:opacity .6s}
.scene.on{opacity:1}
.lbl{font:600 26px Inter;color:#5d5d55;margin:0 0 18px}
h1{font:800 104px/1 'Inter Tight';letter-spacing:-.045em;margin:0 0 24px}
.it{font:italic 400 46px/1.25 'Instrument Serif',serif;color:#2b2b27;margin:0;max-width:1500px}
.term{background:#f4f4ee;border-radius:28px;padding:34px 40px;height:700px;box-sizing:border-box;overflow:hidden;box-shadow:0 30px 70px rgba(15,15,13,.10);
      font:400 25px/1.55 'JetBrains Mono',monospace;display:flex;flex-direction:column;justify-content:flex-end}
.term div{white-space:pre;overflow:hidden;text-overflow:ellipsis}
.think{color:#8c8c83}.call{color:#0f0f0d;font-weight:600}.res{color:#5d5d55}.bad{color:#b83a3a!important;background:rgba(184,58,58,.08)}.ok{color:#16794a!important;background:rgba(22,121,74,.10)}
.bar{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:22px}
.bar h2{font:800 60px 'Inter Tight';letter-spacing:-.03em;margin:0}.bar span{font:600 30px 'JetBrains Mono';color:#5d5d55}
.live{display:inline-block;background:#b83a3a;color:#fff;border-radius:999px;padding:4px 16px;font:600 22px Inter;margin-left:16px;vertical-align:middle}
.big{font:800 150px/1 'Inter Tight';letter-spacing:-.05em}.grid{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:30px}
.card{background:#f4f4ee;border-radius:28px;padding:40px}.card p{font:600 28px Inter;color:#5d5d55;margin:0 0 10px}
</style></head><body>
<div class="scene" id="intro"><p class="lbl">Live recording · real speed · Claude Haiku 4.5 worker</p><h1>Watch Mend fix itself.</h1><p class="it" id="rep"></p></div>
<div class="scene" id="before"><div class="bar"><h2>Original worker<span class="live">LIVE</span></h2><span id="bclock"></span></div><div class="term" id="bterm"></div></div>
<div class="scene" id="diag"><p class="lbl">Supervisor · Claude Opus 5.5 · reads the run back from neatlogs</p><h1>Diagnosis → patch → re-run.</h1>
<p class="it">The worker rewrote a whole file it had only partly read, deleting working code. Mend gave itself a precise edit tool. Kept only because the full re-run got better.</p></div>
<div class="scene" id="after"><div class="bar"><h2>Repaired worker<span class="live">LIVE</span></h2><span id="aclock"></span></div><div class="term" id="aterm"></div></div>
<div class="scene" id="result"><p class="lbl">Same task · same model · both runs traced in neatlogs</p><h1>Fixed, and proven.</h1>
<div class="grid"><div class="card"><p>Original worker</p><div class="big" style="color:#b83a3a" id="r1"></div><p id="r1s"></p></div>
<div class="card"><p>Repaired worker</p><div class="big" style="color:#16794a" id="r2"></div><p id="r2s"></p></div></div></div>
<script>
const D = __DATA__;
document.getElementById('rep').textContent = '“' + D.report + '”';
const fmt = n => n.toLocaleString('en-US');
document.getElementById('r1').textContent = D.before.done.passed ? 'passed' : 'failed';
document.getElementById('r1s').textContent = D.before.done.turns + ' turns · ' + fmt(D.before.done.tokens) + ' tokens · trace ' + D.before.done.trace_id.slice(0,8);
document.getElementById('r2').textContent = D.after.done.passed ? 'passed' : 'failed';
document.getElementById('r2s').textContent = D.after.done.turns + ' turns · ' + fmt(D.after.done.tokens) + ' tokens · trace ' + D.after.done.trace_id.slice(0,8);
const t0 = performance.now(); const shown = {before: 0, after: 0};
function on(id){ document.querySelectorAll('.scene').forEach(s => s.classList.toggle('on', s.id === id)); }
function tick(){
  const t = (performance.now() - t0) / 1000;
  const scene = t < D.before.start ? 'intro' : t < D.diag_at ? 'before' : t < D.after.start ? 'diag' : t < D.result_at ? 'after' : 'result';
  on(scene);
  for (const k of ['before', 'after']) {
    const R = D[k], local = t - R.start, term = document.getElementById(k[0] + 'term');
    while (shown[k] < R.lines.length && R.lines[shown[k]].at <= local) {
      const L = R.lines[shown[k]++], div = document.createElement('div'); div.className = L.cls; div.textContent = L.text; term.appendChild(div);
      while (term.children.length > 18) term.removeChild(term.firstChild);
    }
    if (local >= 0) document.getElementById(k[0] + 'clock').textContent = Math.min(local, R.dur).toFixed(1) + ' s';
  }
  if (t < D.total) requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
</script></body></html>"""


async def tts(narration: list[dict]) -> list[Path]:
    import edge_tts
    files = []
    for i, n in enumerate(narration):
        f = HERE / "vo" / f"{i:02d}.mp3"
        f.parent.mkdir(exist_ok=True)
        await edge_tts.Communicate(n["text"], VOICE).save(str(f))
        files.append(f)
    return files


def duration(f: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))


def record(page: Path, seconds: float) -> tuple[Path, float]:
    """Record the page; also return the lead time between recording start and the page starting to play."""
    import time

    from playwright.sync_api import sync_playwright
    tmp = HERE / "rec"
    tmp.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(tmp),
                            record_video_size={"width": 1920, "height": 1080})
        started = time.time()
        pg = ctx.new_page()
        pg.goto(page.as_uri())
        lead = time.time() - started
        pg.wait_for_timeout(int(seconds * 1000) + 500)
        path = Path(pg.video.path())
        ctx.close()
        b.close()
    return path, lead


def main() -> None:
    data, narration = build()
    # push a voice line later if the previous one would still be speaking
    files = asyncio.run(tts(narration))
    cursor = 0.0
    for n, f in zip(narration, files):
        n["at"] = max(n["at"], cursor + 0.3)
        cursor = n["at"] + duration(f)
    data["total"] = max(data["total"], cursor + 1.5)
    page = HERE / "player.html"
    page.write_text(PAGE.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    (HERE / "narration.json").write_text(json.dumps(narration, indent=2), encoding="utf-8")
    webm, lead = record(page, data["total"])
    inputs, filters = ["-ss", f"{lead:.2f}", "-i", str(webm)], []
    for i, (n, f) in enumerate(zip(narration, files), start=1):
        inputs += ["-i", str(f)]
        ms = int(n["at"] * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(1, len(files) + 1))
    filters.append(f"{mix}amix=inputs={len(files)}:normalize=0,apad[a]")
    out = HERE / "mend-live.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[a]", "-t", f"{data['total']:.2f}", "-c:v", "libx264", "-crf", "22",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    print(f"wrote {out.relative_to(ROOT)} ({data['total']:.1f} s, {out.stat().st_size / 1e6:.1f} MB, trimmed {lead:.2f} s lead)")


if __name__ == "__main__":
    main()
