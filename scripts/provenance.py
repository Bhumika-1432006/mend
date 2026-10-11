"""Who wrote each line of the worker? Entire blame joined to Mend's round records -> evidence/provenance.json

    python scripts/provenance.py      (needs the entire CLI; the site reads the JSON, so CI does not)

Each AI-written line carries its Entire checkpoint, the instruction the supervisor gave Claude Code
(which names the diagnosis file), and the round that diagnosis led to, with the gate's verdict.
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["mend/prompts/worker.md", "mend/worker.py"]


def rounds_by_commit() -> dict[str, dict]:
    out = {}
    for i, p in enumerate(sorted((ROOT / "runs").glob("*.round.json")), 1):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("commit"):
            diag = r["diagnosis"].replace("\\", "/")
            m = re.search(r"## Chosen fix: (.+)", (ROOT / diag).read_text(encoding="utf-8"))
            out[r["commit"][:7]] = {"round": i, "title": r.get("title") or (m.group(1) if m else ""), "kept": r["kept"], "diagnosis": diag}
    return out


def blame(path: str, rounds: dict) -> dict:
    raw = subprocess.run(["entire", "blame", path, "--json"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", timeout=300, check=True).stdout
    data = json.loads(raw)
    lines = []
    for ln in data["lines"]:
        d = re.search(r"runs[\\/]([\w-]+)\.diagnosis\.md", ln.get("prompt", ""))
        lines.append({"n": ln["line_number"], "by": ln["authorship"], "commit": ln["short_commit_sha"][:7],
                      "checkpoint": ln.get("checkpoint_id", ""), "model": ln.get("model", ""),
                      "diagnosis": f"runs/{d.group(1)}.diagnosis.md" if d else "",
                      "round": rounds.get(ln["short_commit_sha"][:7]), "text": ln["content"]})
    return {"file": path, "summary": data["summary"], "lines": lines}


if __name__ == "__main__":
    rounds = rounds_by_commit()
    out = {f: blame(f, rounds) for f in FILES}
    (ROOT / "evidence" / "provenance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for f, b in out.items():
        print(f, b["summary"])
