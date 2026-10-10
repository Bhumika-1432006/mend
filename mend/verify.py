"""Recompute the README's numbers from the run files and fail if any of them does not match.

    python -m mend.verify

Checks (1) every run file is internally consistent (passed count and token totals equal the sum of
its tasks) and (2) the README's result tables contain exactly the numbers the run files give.
"""

import json
import sys

from mend.tasks import ROOT

RUNS = ROOT / "runs"
README = (ROOT / "README.md").read_text(encoding="utf-8")


def runs() -> dict[str, dict]:
    return {json.loads(p.read_text(encoding="utf-8"))["run_id"]: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(RUNS.glob("*.json")) if p.name.count(".") == 1}


def tokens(r: dict) -> int:
    return r["input_tokens"] + r["output_tokens"]


def pct(a: float, b: float) -> str:
    return f"{(b - a) / a * 100:+.1f}%".replace("-", "−")


def expected_strings(rs: dict[str, dict]) -> list[str]:
    out = []
    for p in sorted(RUNS.glob("*.round.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("rejected"):
            continue
        out.append(f"{r['before_passed']} → {r['after_passed']} / {r['total']}")
        out.append(f"{r['before_tokens']:,} → {r['after_tokens']:,} ({pct(r['before_tokens'], r['after_tokens'])})")

    def group(pred):
        return [r for r in rs.values() if pred(r)]

    v0 = group(lambda r: r["total"] == 28 and r["worker_commit"] == "13defdb" and "haiku" in r["model"])
    r1 = [rs[i] for i in ("2026-10-10T09-31-07-after", "2026-10-10T09-40-55", "2026-10-10T09-51-17") if i in rs]
    if v0 and r1:
        mb, ma = (sum(map(tokens, g)) / len(g) for g in (v0, r1))
        out += [", ".join(str(r["passed"]) for r in v0), f"{mb:,.0f}", ", ".join(str(r["passed"]) for r in r1),
                f"{ma:,.0f} ({pct(mb, ma)})"]
    hb = group(lambda r: r.get("heldout") and r["worker_commit"] == "13defdb")
    ha = group(lambda r: r.get("heldout") and r["worker_commit"] != "13defdb")
    if hb and ha:
        mb, ma = (sum(map(tokens, g)) / len(g) for g in (hb, ha))
        out += [f"{', '.join(str(r['passed']) for r in hb)} of {hb[0]['total']}", f"{mb:,.0f}",
                f"{', '.join(str(r['passed']) for r in ha)} of {ha[0]['total']}", f"{ma:,.0f} ({pct(mb, ma)})"]
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rs = runs()
    problems = []
    for rid, r in rs.items():
        if r["passed"] != sum(t["passed"] for t in r["tasks"]) or r["total"] != len(r["tasks"]):
            problems.append(f"{rid}: passed/total do not match its tasks")
        if r.get("input_tokens", 0) != sum(t.get("input_tokens", 0) for t in r["tasks"]):
            problems.append(f"{rid}: input_tokens do not match its tasks")
    checks = expected_strings(rs)
    for s in checks:
        if s not in README:
            problems.append(f"README is missing the number computed from run files: {s!r}")
    print(f"{len(rs)} run files, {len(checks)} README numbers recomputed")
    for s in checks:
        print(f"  {'ok ' if s in README else 'BAD'} {s}")
    for p in problems:
        print("FAIL", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
