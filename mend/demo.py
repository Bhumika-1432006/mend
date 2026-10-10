"""Demo mode for the landing page: index.html?demo=1 replays the first self-repair from saved evidence.

Everything shown comes from files: the task's bug report (tasks/tasks.json), the before/after
tool-call traces read back from neatlogs (evidence/task23-*-trace.json), the supervisor's
diagnosis (runs/*.diagnosis.md) and the round record (runs/*.round.json). No network calls.
"""

import json
import re

from mend.tasks import ROOT, load_tasks

TASK = "23"


def _cause(diagnosis_file: str) -> str:
    text = (ROOT / diagnosis_file).read_text(encoding="utf-8")
    row = next((line for line in text.splitlines() if line.startswith(f"| {TASK} |")), "")
    cells = [c.strip() for c in row.strip("|").split("|")]
    return cells[2] if len(cells) > 2 else ""


def _steps(trace: dict) -> list[dict]:
    out = []
    for call in trace["tool_calls"]:
        args = call["args"]
        detail = args.get("path", args.get("pattern", ""))
        if call["tool"] == "run_tests" and not detail:
            detail = "full suite"
        if call["tool"] == "write_file":
            detail += f" · {args.get('content', '')}"
        first = call["output"].split("\n")[0][:70]
        flag = ""
        if call["tool"] == "write_file":
            flag = "bad"
        elif call["tool"] == "edit_file":
            flag = "ok"
        elif call["tool"] == "run_tests":
            flag = "ok" if first.startswith("PASSED") else "bad"
        out.append({"tool": call["tool"], "detail": detail[:90], "out": first, "flag": flag})
    return out


def demo_data(first_round: dict, round_title: str) -> dict | None:
    try:
        before = json.loads((ROOT / "evidence/task23-before-trace.json").read_text(encoding="utf-8"))
        after = json.loads((ROOT / "evidence/task23-after-trace.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    report = next(t["report"] for t in load_tasks() if t["id"] == TASK)
    diag = first_round["diagnosis"].replace("\\", "/")
    return {
        "task": TASK, "report": report,
        "before": {"steps": _steps(before), "turns": before["turns"], "trace": before["trace_id"][:8]},
        "after": {"steps": _steps(after), "turns": after["turns"], "trace": after["trace_id"][:8]},
        "cause": re.sub(r"\s+", " ", _cause(diag))[:420], "fix": round_title, "commit": first_round["commit"],
        "score": [first_round["before_passed"], first_round["after_passed"], first_round["total"]],
        "tokens": [first_round["before_tokens"], first_round["after_tokens"]],
    }


CSS = """
#demo{position:fixed;inset:0;background:rgba(230,230,221,.97);z-index:50;display:none;align-items:center;justify-content:center;padding:24px}
#demo.on{display:flex} #demo .box{width:min(980px,100%);background:#f4f4ee;border-radius:24px;padding:32px;box-shadow:0 30px 80px rgba(15,15,13,.15)}
#demo .lbl{font:600 13px Inter,sans-serif;color:#5d5d55;margin:0 0 10px} #demo h3{font:800 clamp(28px,4vw,44px)/1 'Inter Tight',sans-serif;letter-spacing:-.03em;margin:0 0 14px}
#demo .it{font:italic 400 22px/1.35 'Instrument Serif',Georgia,serif;color:#3a3a35;margin:0}
#demo ol{list-style:none;margin:16px 0 0;padding:0;font:13px/1.45 'JetBrains Mono',monospace;max-height:52vh;overflow:auto}
#demo li{display:grid;grid-template-columns:110px 1fr;gap:12px;padding:6px 10px;border-radius:8px;opacity:0;transform:translateY(6px);transition:all .35s}
#demo li.in{opacity:1;transform:none} #demo li.bad{background:rgba(184,58,58,.10)} #demo li.ok{background:rgba(22,121,74,.10)}
#demo li b{font-weight:600} #demo li span{color:#5d5d55;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#demo .row{display:flex;justify-content:space-between;align-items:center;margin-top:20px;gap:12px;flex-wrap:wrap}
#demo .dots i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#cbcbbf;margin-right:6px} #demo .dots i.on{background:#0f0f0d}
#demo .hint{font-size:13px;color:#5d5d55} #demo .num{font:800 64px/1 'Inter Tight',sans-serif;letter-spacing:-.04em}
#demo .ok{color:#16794a} #demo .bad{color:#b83a3a}
@media (prefers-reduced-motion:reduce){#demo li{transition:none}}
"""

JS = r"""
(function(){
  var D = window.MEND_DEMO; if (!D || new URLSearchParams(location.search).get('demo') !== '1') return;
  var el = document.getElementById('demo'); el.classList.add('on');
  var box = el.querySelector('.box'), dots = el.querySelector('.dots'), i = 0, timer = null;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function list(steps){ return '<ol>' + steps.map(function(s){ return '<li class="'+s.flag+'"><b>'+esc(s.tool)+'</b><span>'+esc(s.detail)+(s.out?' → '+esc(s.out):'')+'</span></li>'; }).join('') + '</ol>'; }
  var fmt = function(n){ return n.toLocaleString('en-US'); };
  var scenes = [
    {t: 6000, h: '<p class="lbl">Task '+D.task+' · original worker</p><h3>A user reports a bug.</h3><p class="it">“'+esc(D.report)+'”</p>'},
    {t: 0, h: '<p class="lbl">neatlogs trace '+D.before.trace+' · '+D.before.turns+' turns, failed</p><h3>The worker tries, and breaks things.</h3>'+list(D.before.steps), steps: true},
    {t: 9000, h: '<p class="lbl">Supervisor · diagnosis from the trace</p><h3>Found it.</h3><p class="it">'+esc(D.cause)+'</p>'},
    {t: 7000, h: '<p class="lbl">Patch · written by Claude Code · commit '+esc(D.commit)+'</p><h3>Mend fixes itself.</h3><p class="it">'+esc(D.fix)+'</p>'},
    {t: 0, h: '<p class="lbl">neatlogs trace '+D.after.trace+' · same task, new worker</p><h3>Re-run: one precise edit.</h3>'+list(D.after.steps), steps: true},
    {t: 9000, h: '<p class="lbl">Kept, because the numbers improved</p><h3><span class="num bad">'+D.score[0]+'</span> → <span class="num ok">'+D.score[1]+'</span> <span class="it">of '+D.score[2]+' tasks</span></h3><p class="it">Tokens '+fmt(D.tokens[0])+' → '+fmt(D.tokens[1])+'. Every fix is gated like this: keep it only if a full re-run gets better.</p>'}
  ];
  function show(n){
    clearTimeout(timer); i = n; if (i >= scenes.length) { el.classList.remove('on'); return; }
    box.querySelector('.scene').innerHTML = scenes[i].h;
    dots.innerHTML = scenes.map(function(_, k){ return '<i class="'+(k===i?'on':'')+'"></i>'; }).join('');
    if (scenes[i].steps) {
      var lis = box.querySelectorAll('li'), k = 0;
      (function next(){ if (k < lis.length) { lis[k++].classList.add('in'); timer = setTimeout(next, 650); } else { timer = setTimeout(function(){ show(i+1); }, 2500); } })();
    } else { timer = setTimeout(function(){ show(i+1); }, scenes[i].t); }
  }
  el.addEventListener('click', function(){ show(i+1); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') { clearTimeout(timer); el.classList.remove('on'); } if (e.key === ' ' || e.key === 'ArrowRight') { e.preventDefault(); show(i+1); } });
  show(0);
})();
"""


def demo_block(first_round: dict | None, round_title: str) -> str:
    data = demo_data(first_round, round_title) if first_round else None
    if not data:
        return ""
    payload = json.dumps(data).replace("</", "<\\/")
    return (f"<style>{CSS}</style>"
            '<div id="demo" role="dialog" aria-label="Self-repair replay"><div class="box"><div class="scene"></div>'
            '<div class="row"><div class="dots"></div><span class="hint">click or space: next · Esc: close</span></div></div></div>'
            f"<script>window.MEND_DEMO={payload};</script><script>{JS}</script>")
